"""Resolve a CVE to public remediation metadata and cache each source independently."""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile
from urllib.parse import urlencode
from urllib.request import Request, urlopen

CVE_ID = re.compile(r"CVE-[0-9]{4}-[0-9]{4,}", re.IGNORECASE)
GHSA_ID = re.compile(r"GHSA-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{4}")
MAX_BYTES = 8 * 1024 * 1024
VISIBLE_VERSION_CRITERIA = 8


def fetch_json(url: str):
    headers = {"Accept": "application/json", "User-Agent": "brain-defense"}
    with urlopen(Request(url, headers=headers), timeout=8) as response:
        data = response.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ValueError("Response exceeded the size limit")
    return json.loads(data)


def nvd_details(cve: str) -> dict:
    query = urlencode({"cveId": cve})
    payload = fetch_json(f"https://services.nvd.nist.gov/rest/json/cves/2.0?{query}")
    records = [item["cve"] for item in payload.get("vulnerabilities", [])]
    record = next((item for item in records if item["id"] == cve), None)
    if record is None:
        raise ValueError("CVE not found in NVD")

    affected = []
    bounds = ("versionStartIncluding", "versionStartExcluding", "versionEndIncluding", "versionEndExcluding")
    for configuration in record.get("configurations", []):
        for node in configuration.get("nodes", []):
            for match in node.get("cpeMatch", []):
                if match.get("vulnerable") is True:
                    criteria = {"cpe": match["criteria"], **{key: match[key] for key in bounds if key in match}}
                    if criteria not in affected:
                        affected.append(criteria)
    kev_date = record.get("cisaExploitAdd")
    return {
        "last_modified": record.get("lastModified"),
        "kev_added": kev_date,
        "kev_required_action": record.get("cisaRequiredAction") if kev_date else None,
        "affected_cpe": affected,
    }


def github_details(cve: str) -> list[dict]:
    query = urlencode({"cve_id": cve, "type": "reviewed", "per_page": 100})
    payload = fetch_json(f"https://api.github.com/advisories?{query}")
    if not isinstance(payload, list):
        raise ValueError("Unexpected GitHub response")
    packages = []
    for advisory in payload:
        ghsa = advisory["ghsa_id"]
        if advisory.get("cve_id") != cve or advisory.get("withdrawn_at") or not GHSA_ID.fullmatch(ghsa):
            continue
        for entry in advisory.get("vulnerabilities", []):
            package = entry["package"]
            fixed = entry.get("first_patched_version")
            if isinstance(fixed, dict):
                fixed = fixed.get("identifier")
            packages.append({
                "ecosystem": package["ecosystem"], "package": package["name"],
                "affected": entry.get("vulnerable_version_range"),
                "first_patched_version": fixed,
                "source": f"https://github.com/advisories/{ghsa}",
            })
    return packages


def cache_directory() -> Path:
    override = os.environ.get("BRAIN_CACHE_DIR")
    if override:
        return Path(override)
    base = os.environ.get("LOCALAPPDATA" if sys.platform == "win32" else "XDG_CACHE_HOME")
    directory = Path(base) if base else Path.home() / ".cache"
    return directory / "brain-defense"


def read_cache(path: Path, cve: str, source: str) -> dict | None:
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
        entry = record["entry"]
        expected_type = dict if source == "nvd" else list
        if (record["cve"] == cve and record["source"] == source
                and isinstance(entry["checked_at"], str) and isinstance(entry["details"], expected_type)):
            return entry
    except (OSError, ValueError, KeyError, TypeError):
        pass
    return None


def save_cache(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as output:
        temporary = Path(output.name)
        try:
            json.dump(record, output, ensure_ascii=False)
            output.close()
            temporary.replace(path)
        finally:
            temporary.unlink(missing_ok=True)


def get_advisory(cve: str, refresh: bool) -> dict:
    sources = {
        "CVE Program": f"https://www.cve.org/CVERecord?id={cve}",
        "NIST NVD": f"https://nvd.nist.gov/vuln/detail/{cve}",
        "CISA KEV": "https://www.cisa.gov/known-exploited-vulnerabilities-catalog",
    }
    directory = cache_directory()
    data = {}
    record = {"cve": cve, "sources": sources, "data": data, "warnings": []}
    for source, load in (("nvd", nvd_details), ("github", github_details)):
        path = directory / f"{cve}-{source}.json"
        entry = read_cache(path, cve, source)
        if refresh:
            try:
                details = load(cve)
            except (OSError, ValueError, KeyError, TypeError, AttributeError) as error:
                record["warnings"].append(f"Could not refresh {source}: {error}")
            else:
                entry = {
                    "checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    "details": details,
                }
                try:
                    save_cache(path, {"cve": cve, "source": source, "entry": entry})
                except OSError as error:
                    record["warnings"].append(f"Could not cache {source}: {error}")
        if entry is not None:
            data[source] = entry
    return record


def format_advisory(record: dict) -> str:
    lines = [record["cve"]]
    lines.extend(f"  {name}  {url}" for name, url in record["sources"].items())
    nvd = record["data"].get("nvd")
    github = record["data"].get("github")
    if github:
        lines.append(f"\nReviewed GitHub advisories checked {github['checked_at']}")
        for package in github["details"]:
            lines.append(
                f"  {package['ecosystem']} / {package['package']}  "
                f"affected {package['affected'] or 'unknown'}  "
                f"first patched {package['first_patched_version'] or 'unknown'}  {package['source']}"
            )
        if not github["details"]:
            lines.append("  No matching package versions in reviewed advisories.")
    if nvd:
        details = nvd["details"]
        lines.append(f"\nNVD metadata checked {nvd['checked_at']}")
        lines.append(f"  CISA KEV added  {details.get('kev_added') or 'unknown'}")
        if details.get("kev_required_action"):
            lines.append(f"  Required action  {details['kev_required_action']}")
        criteria = details.get("affected_cpe", [])
        if criteria:
            lines.append(f"  {len(criteria)} version criteria (see NVD for complete applicability conditions)")
            for row in criteria[:VISIBLE_VERSION_CRITERIA]:
                bounds = ", ".join(f"{key}={value}" for key, value in row.items() if key != "cpe")
                lines.append(f"    {row['cpe']}" + (f"  {bounds}" if bounds else ""))
            if len(criteria) > VISIBLE_VERSION_CRITERIA:
                lines.append("    Use --json to see all version criteria.")
    if not record["data"]:
        lines.append("\nNo cached remediation details. Add --refresh to retrieve public metadata.")
    return "\n".join(lines)
