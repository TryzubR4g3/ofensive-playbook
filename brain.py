#!/usr/bin/env python3
"""
brain — CLI index for the Writeups second-brain.

Zero-dependency Python 3. Works on Linux and Git Bash on Windows.

Usage
-----
  brain guide                    Beginner examples and search recipes.
  brain <topic> [keyword]        Search inside a curated topic scope.
                                 `brain enumeration find` → every `find`
                                 command in enumeration tools/exploits,
                                 with file:line.
  brain topics                   List every topic and what it covers.

  brain find <query>             Beginner-friendly alias for `search`.
  brain search <query>           Case-insensitive grep across every .md.
  brain cmd    <query>           Grep inside fenced ``` code blocks only.

  brain tool    [name]           Show a tool note (or list all).
  brain exploit [name]           Show an exploit note (or list all).
  brain payload [name]           Show a payload/snippet note (or list all).
  brain writeup [name]           Show a writeup (or list all).
  brain list    [tools|exploits|payloads|writeups|all]

  brain used-on <Machine>        Every note tagged "Used on: <Machine>".
  brain backrefs <note>          Every writeup that links to <note>.
  brain open    <path>           Open in $EDITOR (falls back to cat).

  brain --color=always <cmd>      Force ANSI color output.
  brain --color=never <cmd>       Disable ANSI color output.

Tool notes do not store writeup backlink lists. Writeups link to notes, and
`brain backrefs <note>` derives backlinks from those writeup links when you
need to see where a technique was used.

Examples
--------
  brain enumeration find                      # find commands I've used for enum
  brain fuzz ffuf                             # every ffuf invocation tagged
  brain privesc sudo                          # privesc-scoped "sudo" hits
  brain creds grep                            # credential-hunting greps
  brain shells                                # all reverse-shell one-liners
  brain web curl                              # curl usage in web exploits
  brain ad kerberos                           # AD/Kerberos-specific commands
  brain find "nc -lvnp"                       # broad search when unsure
  brain cmd "find /"                          # command-block-only search
"""
from __future__ import annotations

import os
import re
import sys
import subprocess
from pathlib import Path
from typing import Iterable, NamedTuple

# Force UTF-8 stdout on Windows consoles (cp1252 breaks on any non-ASCII)
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    except Exception:
        pass

ROOT = Path(__file__).resolve().parent
DIRS = {
    "tools":    [ROOT / "tools"],
    "exploits": [ROOT / "exploits"],
    "privesc":  [ROOT / "privesc"],
    "playbooks": [ROOT / "playbooks"],
    "techniques": [ROOT / "techniques"],
    "payloads": [ROOT / "payloads"],
    "writeups": [ROOT / "writeups" / "HTB" / "Easy",
                 ROOT / "writeups" / "HTB" / "Medium",
                 ROOT / "writeups" / "HTB" / "Hard",
                 ROOT / "writeups" / "HTB" / "ProLabs",
                 ROOT / "writeups" / "OffSec" / "Easy",
                 ROOT / "writeups" / "OffSec" / "Medium",
                 ROOT / "writeups" / "OffSec" / "Hard",
                 ROOT / "writeups" / "TRY" / "Easy",
                 ROOT / "writeups" / "TRY" / "Medium",
                 ROOT / "writeups" / "TRY" / "Hard",
                 ROOT / "writeups" / "TRY" / "Networks" / "Easy",
                 ROOT / "writeups" / "TRY" / "Networks" / "Medium",
                 ROOT / "writeups" / "TRY" / "Networks" / "Hard",
                 ROOT / "writeups" / "Webverselabs" / "Challenges",
                 ROOT / "writeups" / "Webverselabs" / "Labs" / "Easy"],
}

# ---- ANSI colors ----
_COLOR_MODE = os.environ.get("BRAIN_COLOR", "auto").lower()
_USE_COLOR = (
    os.environ.get("NO_COLOR") is None
    and _COLOR_MODE != "never"
    and (_COLOR_MODE == "always" or sys.stdout.isatty())
)

if sys.platform == "win32" and _USE_COLOR:
    os.system("")


def configure_color(argv: list[str]) -> list[str]:
    global _USE_COLOR, _COLOR_MODE
    cleaned: list[str] = []
    for arg in argv:
        if arg == "--color":
            _COLOR_MODE = "always"
        elif arg == "--no-color":
            _COLOR_MODE = "never"
        elif arg.startswith("--color="):
            _COLOR_MODE = arg.split("=", 1)[1].lower()
        else:
            cleaned.append(arg)
            continue

        if _COLOR_MODE not in {"auto", "always", "never"}:
            print("usage: brain [--color=auto|always|never] <command> [args]", file=sys.stderr)
            sys.exit(2)

        _USE_COLOR = (
            os.environ.get("NO_COLOR") is None
            and _COLOR_MODE != "never"
            and (_COLOR_MODE == "always" or sys.stdout.isatty())
        )
    return cleaned


def _c(text: str, code: str) -> str:
    return f"\x1b[{code}m{text}\x1b[0m" if _USE_COLOR else text
def bold(s):   return _c(s, "1")
def dim(s):    return _c(s, "2")
def green(s):  return _c(s, "32")
def yellow(s): return _c(s, "33")
def cyan(s):   return _c(s, "36")
def red(s):    return _c(s, "31")
def blue(s):   return _c(s, "34")


# ---- Topics ----
# Each topic resolves to a union of:
#   tools        = exact tool stems in tools/
#   exploits     = substrings that must appear in exploit filenames
#   payloads     = substrings that must appear in payload filenames
#   all_exploits = include every file in exploits/
#   all_payloads = include every file in payloads/
TOPICS: dict[str, dict] = {
    "recon": {
        "desc": "Port scan, banner grab, directory brute, service banners",
        "tools": ["nmap", "silent-scan", "whatweb", "searchsploit", "enum4linux", "showmount", "ftp",
                  "smbclient", "smbmap", "nuclei", "feroxbuster", "ffuf",
                  "gobuster", "wget", "proxychains", "foxyproxy", "ldap-utils",
                  "onesixtyone", "snmpwalk", "snmpset", "nikto", "bloodhound", "find", "grep"],
        "exploits": ["smb-anonymous-enum", "anonymous-ftp-enumeration",
                     "smb-enumeration", "rid-brute-enumeration", "snmp",
                     "web-discovery", "file-transfers"],
    },
    "enumeration": {
        "desc": "Post-foothold system / AD / network enumeration",
        "tools": ["nmap", "enum4linux", "netexec", "smbclient", "impacket", "kerbrute",
                  "bloodhound", "showmount", "ftp", "redis-cli", "rsync", "mysql",
                  "mongo", "sqlite3", "ffuf", "gobuster", "feroxbuster", "getcap",
                  "proxychains", "powershell-empire", "smbmap", "nuclei", "ldap-utils",
                  "onesixtyone", "snmpwalk", "snmpset", "find", "grep"],
        "exploits": ["enum", "linux-enumeration", "windows-enumeration",
                     "smb-enumeration", "smb-anonymous-enum", "mssql-enumeration",
                     "rid-brute-enumeration", "anonymous-ftp-enumeration",
                     "env-variable-enum", "docker-container-enumeration",
                     "mongodb-enumeration", "windows-sam-hive-dump",
                     "nfs-mounted-file-loot", "docker-container-secret-hunting",
                     "nfs-uid-hijack", "snmp", "asterisk-ami", "nosql-where-injection"],
    },
    "fuzz": {
        "desc": "Directory / vhost / parameter fuzzing",
        "tools": ["ffuf", "gobuster", "feroxbuster"],
        "exploits": [],
    },
    "exploit": {
        "desc": "All exploit playbooks",
        "tools": [],
        "all_exploits": True,
    },
    "privesc": {
        "desc": "Local privilege escalation (Linux + Windows)",
        "tools": ["getcap", "runas"],
        "exploits": ["sudo-", "docker-group-escape", "pkexec", "fail2ban",
                     "cron-script-abuse", "gogs-symlink-attack", "nfs-share-abuse",
                     "rsync-module-abuse", "nssm-service-abuse", "bash-eval-filter",
                     "shadow-credentials", "linux-capabilities-privesc",
                     "sudo-cat-file-read", "suid-env-var-checker",
                     "suid-binary-reversing", "exiftool-sudo",
                     "systemd-service-privesc", "windows-unquoted-service-path",
                     "suid-path-hijack", "tar-wildcard-injection",
                     "python-library-hijack", "suid-python",
                     "yum-sudo-plugin-injection", "printspoofer-seimpersonate", "nodejs-inspector",
                     "gdb-suid-privesc", "java-cron-symlink", "sudo-binary-rop-gets",
                     "suid-find-escape"],
    },
    "shells": {
        "desc": "Reverse-shell one-liners and listener patterns",
        "tools": ["netcat", "socat", "ssh", "sshpass", "evil-winrm", "impacket", "metasploit", "msfvenom",
                  "chisel", "plink"],
        "exploits": [],
        "all_payloads": True,
        "keywords": ["bash -i", "/dev/tcp/", "nc -lvnp", "pty.spawn",
                     "socat", "mkfifo", "stty raw -echo", "powershell -enc"],
    },
    "payloads": {
        "desc": "Reusable payload snippets, webshells and shell stabilization",
        "tools": ["netcat", "socat", "ssh", "msfvenom"],
        "exploits": [],
        "all_payloads": True,
    },
    "creds": {
        "desc": "Credential hunting, cracking, reuse",
        "tools": ["hashcat", "john", "gpg", "tcpdump", "strings", "responder",
                  "mimikatz", "hydra", "ldap-utils"],
        "exploits": ["cred", "bash-history-credentials", "env-variable-enum",
                     "env-file-exposure", "ntlm-capture-crack", "pgp-key-cracking",
                     "password-spraying", "kerberos-roasting", "shadow-credentials",
                     "tcpdump-credential-sniffing", "binary-credential-hunting",
                     "systemd-service-credentials", "backup-file-exposure",
                     "base64-encoded-credentials", "mimikatz-sam-pth",
                     "windows-sam-hive-dump", "wordpress-wp-config-credentials",
                     "firefox-credential-extraction", "mcp-admin-dump-credential-leak",
                     "jenkins-http-form-bruteforce", "ldap-passback-attack", "asreproast",
                     "nosql-json-login-bypass", "nosql-where-injection"],
    },
    "ad": {
        "desc": "Active Directory / Kerberos / SMB / LDAP",
        "tools": ["netexec", "impacket", "kerbrute", "smbclient", "evil-winrm",
                  "dnstool", "responder", "bloodhound", "mimikatz", "xfreerdp",
                  "hydra", "ldap-utils", "runas"],
        "exploits": ["adidns-poisoning", "kerberos-roasting", "password-spraying",
                     "smb-anonymous-enum", "smb-enumeration", "shadow-credentials",
                     "rid-brute-enumeration", "mssql-", "ntlm-capture-crack",
                     "windows-enumeration", "smb-write-iis-execution",
                     "base64-encoded-credentials", "mimikatz-sam-pth",
                     "windows-admin-stabilization", "windows-sam-hive-dump",
                     "ldap-passback-attack", "asreproast"],
    },
    "web": {
        "desc": "Web / HTTP exploitation",
        "tools": ["curl", "sqlmap", "ffuf", "gobuster", "feroxbuster", "wget",
                  "whatweb", "exiftool", "gittools", "wpscan", "nuclei", "padre",
                  "metasploit", "msfvenom", "nikto"],
        "exploits": ["sweetrice-media-center-rce", "magnusbilling-rce",
                     "cacti-rce", "apache-cxf-xop-lfi", "oscommerce-installer-rce",
                     "zoneminder-sqli", "backup-file-exposure", "lfi-php-parameter",
                     "env-file-exposure", "url-param-command-injection",
                     "codiad-rce", "mailhog-password-reset",
                     "hoverfly-middleware-rce", "motioneye-config-injection",
                     "wcf-soap-injection", "flowise-mcp-rce", "mcp-api-injection",
                     "mcp-admin-dump-credential-leak",
                     "teamcity-superuser-token-rce",
                     "werkzeug-debug-rce", "apache-path-traversal-rce",
                     "hidden-parameter-fuzzing", "ds-store-disclosure",
                     "omigod-rce", "cockpit-cms-rce", "python-input-injection",
                     "php-source-disclosure-lfi", "sql-union-injection",
                     "cuppa-cms-alertconfig-lfi-rfi",
                     "php-extension-bypass-upload", "smb-write-iis-execution",
                     "webmin-cve-2019-15107-rce", "gitstack-rce",
                     "ssrf-internal-port-scan", "cookie-base64-md5-forgery",
                     "php-exiftool-comment-webshell", "wordpress-theme-editor-webshell",
                     "jenkins-script-console-rce", "public-log-invite-code-disclosure",
                     "javascript-obfuscated-api-key", "php-mt-rand-token-prediction",
                     "padding-oracle-command-injection", "fuel-cms-rce",
                     "webdav-upload-rce", "tomcat-manager-war-upload",
                     "wordpress-crop-image-rce", "xpath-login-injection",
                     "smb-write-webroot-php-execution",
                     "git-history-disclosure", "rejetto-hfs-rce",
                     "joomla-com-fields-sqli", "joomla-template-editor-webshell",
                     "sql-injection", "sqli", "blind-sql", "time-based", "in-band",
                     "nosql-json-login-bypass"],
    },
    "xss": {
        "desc": "Cross-site scripting payloads and XSS note types",
        "tools": [],
        "exploits": ["xss", "stored-xss", "reflected-xss", "dom-based-xss", "blind-xss"],
        "payloads": ["xss"],
    },
    "container": {
        "desc": "Container / Docker abuse",
        "tools": ["docker", "getcap"],
        "exploits": ["docker-api-unauthenticated", "docker-group-escape",
                     "docker-container-enumeration", "container-network-pivoting",
                     "linux-capabilities-privesc", "docker-container-secret-hunting"],
    },
    "stego": {
        "desc": "Steganography / metadata loot",
        "tools": ["exiftool", "steghide", "strings"],
        "exploits": ["steganography-image-loot", "pgp-key-cracking",
                     "ds-store-disclosure", "npiet-piet-stego",
                     "php-exiftool-comment-webshell"],
    },
    "sqli": {
        "desc": "SQL injection",
        "tools": ["sqlmap"],
        "exploits": ["zoneminder-sqli", "lfi-php-parameter", "backup-file-exposure",
                     "sql-union-injection", "sql-injection", "sqli", "blind-sql",
                     "time-based", "in-band"],
        "payloads": ["nosql", "mongodb", "xpath", "sql"],
    },
    "lfi": {
        "desc": "Local File Inclusion / arbitrary read",
        "tools": ["curl", "ffuf"],
        "exploits": ["lfi-php-parameter", "apache-cxf-xop-lfi", "env-file-exposure",
                     "cuppa-cms-alertconfig-lfi-rfi",
                     "apache-path-traversal-rce", "ds-store-disclosure",
                     "hidden-parameter-fuzzing", "werkzeug-debug-rce",
                     "php-source-disclosure-lfi", "php-exiftool-comment-webshell",
                     "public-log-invite-code-disclosure", "javascript-obfuscated-api-key"],
    },
    "rce": {
        "desc": "Remote Code Execution chains",
        "tools": ["curl", "metasploit", "msfvenom", "searchsploit"],
        "exploits": ["rce", "url-param-command-injection", "cacti-rce",
                     "codiad-rce", "oscommerce-installer-rce",
                     "sweetrice-media-center-rce", "magnusbilling-rce",
                     "flowise-mcp-rce", "hoverfly-middleware-rce",
                     "teamcity-superuser-token-rce",
                     "werkzeug-debug-rce", "apache-path-traversal-rce",
                     "omigod-rce", "cockpit-cms-rce", "python-input-injection",
                     "php-extension-bypass-upload", "smb-write-iis-execution",
                     "webmin-cve-2019-15107-rce", "gitstack-rce",
                     "php-exiftool-comment-webshell", "wordpress-theme-editor-webshell",
                     "jenkins-script-console-rce", "padding-oracle-command-injection",
                     "fuel-cms-rce", "cuppa-cms-alertconfig-lfi-rfi",
                     "webdav-upload-rce", "tomcat-manager-war-upload",
                     "wordpress-crop-image-rce", "smb-write-webroot-php-execution",
                     "rejetto-hfs-rce", "joomla-com-fields-sqli",
                     "joomla-template-editor-webshell", "react2shell", "nodejs-eval-rce",
                     "asterisk-ami-command-execution"],
    },
    "reversing": {
        "desc": "Binary reverse engineering (SUID, custom binaries)",
        "tools": ["strings", "ltrace", "objdump", "pycdc"],
        "exploits": ["suid-binary-reversing", "sudo-binary-rop-gets", "buffer-overflow-ret2shellcode"],
    },
    "database": {
        "desc": "Backend DB enumeration & abuse (Mongo, SQLite, MySQL, Redis)",
        "tools": ["mongo", "mysql", "sqlite3", "redis-cli"],
        "exploits": ["mongodb-enumeration", "mssql-enumeration",
                     "mssql-linked-server", "redis-auth-abuse",
                     "zoneminder-sqli", "lfi-php-parameter",
                     "sql-union-injection", "nosql-json-login-bypass", "nosql-where-injection"],
        "payloads": ["mongodb", "nosql", "sql"],
    },
    "crypto": {
        "desc": "Token prediction, padding oracles, weak crypto",
        "tools": ["padre", "padbuster"],
        "exploits": ["php-mt-rand-token-prediction", "padding-oracle-command-injection"],
    },
    "pivot": {
        "desc": "Port forwarding, tunnelling, container-to-host pivot",
        "tools": ["ssh", "nmap", "chisel", "proxychains", "foxyproxy", "plink",
                  "sshuttle", "socat"],
        "exploits": ["ssh-tunneling", "container-network-pivoting",
                     "chisel-pivoting", "powershell-empire-hop-listener", "pivoting-tunnelling"],
    },
}

# Aliases
TOPIC_ALIASES = {
    "enum": "enumeration", "enumeracion": "enumeration", "enumeration": "enumeration",
    "recon": "recon", "reconnaissance": "recon", "reconocimiento": "recon",
    "escalation": "privesc", "shell": "shells", "reverse-shell": "shells",
    "payload": "payloads", "payloads": "payloads", "payloades": "payloads",
    "pivoting": "pivot", "tunel": "pivot", "tunnel": "pivot",
    "active-directory": "ad", "kerberos": "ad", "xss": "xss",
    "cross-site-scripting": "xss",
    "steganography": "stego", "credentials": "creds", "credenciales": "creds",
    "password": "creds", "passwords": "creds", "cred": "creds", "http": "web",
    "reverse": "reversing", "binary": "reversing", "re": "reversing",
    "docker": "container", "containers": "container", "contenedor": "container", "k8s": "container",
    "db": "database", "database": "database", "base-datos": "database",
    "mongodb": "database", "sqlite": "database", "nosql": "database",
    "padding": "crypto", "oracle": "crypto", "weak-crypto": "crypto",
    "privilegios": "privesc", "escalada": "privesc", "windows": "ad",
    "sql": "sqli", "inyeccion-sql": "sqli",
}


# ---- File walkers ----

def iter_category(cat: str) -> Iterable[Path]:
    for d in DIRS[cat]:
        if not d.is_dir():
            continue
        patterns = ["*.md", "*.txt"] if cat == "payloads" else ["*.md"]
        seen: set[Path] = set()
        for pattern in patterns:
            for p in sorted(d.rglob(pattern)):
                if p not in seen:
                    seen.add(p)
                    yield p

def iter_all() -> Iterable[tuple[str, Path]]:
    for cat in ("tools", "exploits", "privesc", "playbooks", "techniques", "payloads", "writeups"):
        for p in iter_category(cat):
            yield cat, p

def relpath(p: Path) -> str:
    try:
        return str(p.relative_to(ROOT))
    except ValueError:
        return str(p)


def read_text(p: Path) -> str:
    encodings = ("utf-8", "utf-8-sig", "cp1252", "latin-1")
    for enc in encodings:
        try:
            return _repair_text(p.read_text(encoding=enc))
        except UnicodeDecodeError:
            continue
        except OSError:
            return ""
    try:
        return _repair_text(p.read_text(encoding="utf-8", errors="replace"))
    except OSError:
        return ""


def _repair_text(text: str) -> str:
    replacements = {
        "\u00e2\u20ac\u201d": "\u2014",
        "\u00e2\u20ac\u201c": "\u2013",
        "\u00e2\u20ac\u2019": "'",
        "\u00e2\u20ac\u02dc": "'",
        "\u00e2\u20ac\u0153": '"',
        "\u00e2\u20ac\u009d": '"',
        "\u00e2\u20ac\u00a2": "\u2022",
        "\u00e2\u20ac\u00a6": "\u2026",
        "\u00e2\u20ac\u00a6": "\u2026",
        "\u00e2\u2020\u2019": "\u2192",
        "\u00e2\u2030\u00a4": "\u2264",
        "\u00e2\u2030\u00a5": "\u2265",
        "\u00c2\u00a0": " ",
        "\u00c2\u00a7": "\u00a7",
        "\u00c2\u00b7": "\u00b7",
        "\u00c3\u2014": "\u00d7",
    }
    for bad, good in replacements.items():
        text = text.replace(bad, good)
    return text

class LineHit(NamedTuple):
    lineno: int
    text: str
    in_code: bool


def scan_markdown(p: Path) -> list[LineHit]:
    text = read_text(p)
    if not text:
        return []
    lines: list[LineHit] = []
    in_code = False
    for i, line in enumerate(text.splitlines(), 1):
        if line.lstrip().startswith("```"):
            in_code = not in_code
            continue
        lines.append(LineHit(i, line.rstrip(), in_code))
    return lines


# ---- Topic resolution ----

def topic_files(name: str) -> list[Path]:
    key = TOPIC_ALIASES.get(name, name)
    spec = TOPICS.get(key)
    if not spec:
        return []
    files: list[Path] = []
    # tools by exact stem
    tool_stems = {s.lower() for s in spec.get("tools", [])}
    for p in iter_category("tools"):
        if p.stem.lower() in tool_stems:
            files.append(p)
    # exploits
    if spec.get("all_exploits"):
        for cat in ("exploits", "privesc", "playbooks", "techniques"):
            files.extend(iter_category(cat))
    else:
        substrs = [s.lower() for s in spec.get("exploits", [])]
        if substrs:
            for cat in ("exploits", "privesc", "playbooks", "techniques"):
                for p in iter_category(cat):
                    stem = p.stem.lower()
                    if any(s in stem for s in substrs):
                        files.append(p)
    if spec.get("all_payloads"):
        files.extend(iter_category("payloads"))
    else:
        payload_substrs = [s.lower() for s in spec.get("payloads", [])]
        if payload_substrs:
            for p in iter_category("payloads"):
                stem = p.stem.lower()
                if any(s in stem for s in payload_substrs):
                    files.append(p)
    # dedupe, preserve order
    seen, out = set(), []
    for p in files:
        if p not in seen:
            seen.add(p); out.append(p)
    return out


# ---- Back-references ----

def backrefs(target: Path) -> list[tuple[Path, int, str]]:
    basename = target.name
    hits: list[tuple[Path, int, str]] = []
    for p in iter_category("writeups"):
        for i, line in enumerate(read_text(p).splitlines(), 1):
            if basename in line:
                hits.append((p, i, line.strip()))
    return hits


# ---- Search primitives ----

def _grep_file(p: Path, pat: re.Pattern, code_only: bool = False) -> list[tuple[int, str]]:
    # Plain-text payload lists: every line is a payload — treat as code-only content
    if p.suffix == ".txt":
        hits = []
        for i, line in enumerate(read_text(p).splitlines(), 1):
            line = line.rstrip()
            if line and pat.search(line):
                hits.append((i, line))
        return hits
    hits: list[tuple[int, str, bool]] = []
    for hit in scan_markdown(p):
        if code_only and not hit.in_code:
            continue
        if pat.search(hit.text):
            hits.append((hit.lineno, hit.text, hit.in_code))
    hits.sort(key=lambda x: (not x[2], x[0]))
    return [(h[0], h[1]) for h in hits]


def _looks_command_like(query: str) -> bool:
    command_markers = (
        " -", "--", "/", "\\", "$", "|", ">", "<", "=", "http", ".php", ".py",
        "curl", "nmap", "ffuf", "feroxbuster", "gobuster", "sqlmap", "hydra",
        "nc ", "ssh", "smbclient", "python", "bash", "find ", "grep ", "git ",
    )
    q = query.lower()
    return any(marker in q for marker in command_markers)


def _topic_hits(p: Path, pat: re.Pattern, query: str) -> list[tuple[int, str]]:
    scanned = scan_markdown(p)
    if not scanned:
        return []

    code_hits = [(h.lineno, h.text) for h in scanned if h.in_code and pat.search(h.text)]
    prose_hits = [(h.lineno, h.text) for h in scanned if not h.in_code and pat.search(h.text)]

    if _looks_command_like(query):
        return code_hits

    return code_hits + prose_hits


# ---- Commands ----


def cmd_stats(argv: list[str]) -> int:
    counts = {cat: sum(1 for _ in iter_category(cat)) for cat in DIRS}
    topics_count = len(TOPICS)
    machines = set()
    for cat, p in iter_all():
        if cat in ("tools", "exploits", "privesc", "playbooks", "techniques", "payloads"):
            text = read_text(p)
            for line in text.splitlines():
                if "Used on:" in line:
                    import re
                    m = re.search(r"Used on:\s*\*\*(.*)\*\*", line, re.IGNORECASE)
                    if m:
                        for mac in m.group(1).split(","):
                            machines.add(mac.strip())
    print(f"{counts.get('tools',0)} tools · {counts.get('exploits',0)} exploits · {counts.get('privesc',0)} privesc · {counts.get('techniques',0)} techniques · {counts.get('playbooks',0)} playbooks · {counts.get('payloads',0)} payloads · {counts.get('writeups',0)} writeups")
    print(f"{topics_count} topics · {len(machines)} machines tracked")
    return 0

def cmd_topics(_: list[str]) -> int:
    print(bold("Topics (usage: brain <topic> [keyword])\n"))
    for name, spec in TOPICS.items():
        desc = spec.get("desc", "")
        print(f"  {cyan(name):<18}  {desc}")
    print()
    print(dim("Aliases: " + ", ".join(f"{a}->{t}" for a, t in TOPIC_ALIASES.items())))
    return 0


def cmd_guide(_: list[str]) -> int:
    print(bold("Brain quick guide\n"))
    print("If you know the phase:")
    print(f"  {cyan('brain recon nmap'):<34} port scans and service discovery")
    print(f"  {cyan('brain enum find'):<34} Linux/Windows enumeration commands")
    print(f"  {cyan('brain privesc sudo'):<34} local privilege escalation notes")
    print(f"  {cyan('brain creds password'):<34} credential hunting and cracking")
    print(f"  {cyan('brain web curl'):<34} HTTP payloads and web exploitation")
    print()
    print("If you only remember one word:")
    print(f"  {cyan('brain find nc -lvnp'):<34} search every markdown note")
    print(f"  {cyan('brain cmd \"find /\"'):<34} search only fenced command blocks")
    print(f"  {cyan('brain used-on Overwatch'):<34} all notes tagged with one machine")
    print()
    print("If you want the full note:")
    print(f"  {cyan('brain tool nmap'):<34} show a tool note")
    print(f"  {cyan('brain exploit shadow'):<34} show a technique note")
    print(f"  {cyan('brain backrefs nmap'):<34} writeups that link to that note")
    print()
    print(dim("Tip: topic aliases work too: enum, docker, db, credenciales, privilegios."))
    return 0


def cmd_topic(topic: str, argv: list[str]) -> int:
    files = topic_files(topic)
    if not files:
        print(red(f"No files in topic '{topic}'."))
        print(dim("Try `brain topics`, `brain guide`, or `brain find <keyword>`.")); return 1
    # No keyword — list scope
    if not argv:
        spec = TOPICS.get(TOPIC_ALIASES.get(topic, topic), {})
        keywords = spec.get("keywords", [])
        if keywords:
            pat = re.compile("|".join(re.escape(k) for k in keywords), re.IGNORECASE)
            total = 0
            print(bold(f"Topic: {topic}  ({len(files)} files, keyword hints)"))
            for p in files:
                hits = _grep_file(p, pat, code_only=True)
                if not hits:
                    continue
                total += len(hits)
                print(f"\n{bold(green(relpath(p)))}")
                shown = 0
                for i, line in hits:
                    if shown >= 5:
                        print(dim(f"  ... (+{len(hits) - 5} more — run: brain open {relpath(p)})"))
                        break
                    line = line if len(line) <= 120 else line[:119] + "…"
                    highlight = pat.sub(lambda m: yellow(m.group(0)), line)
                    print(f"  :{i}  {highlight}")
                    shown += 1
            if total:
                print(dim(f"\n{total} topic hint(s). Add a keyword for a narrower search."))
                return 0
        print(bold(f"Topic: {topic}  ({len(files)} files)"))
        for p in files:
            print(f"  {cyan(relpath(p))}")
        print(dim("\nAdd a keyword to grep inside this scope, e.g. "
                  f"`brain {topic} <keyword>`."))
        return 0
    # Keyword grep within topic
    query = " ".join(argv)
    pat = re.compile(re.escape(query), re.IGNORECASE)
    total = 0
    for p in files:
        hits = _topic_hits(p, pat, query)
        if not hits:
            continue
        total += len(hits)
        print(f"\n{bold(green(relpath(p)))}")
        shown = 0
        for i, line in hits:
            if shown >= 5:
                print(dim(f"  ... (+{len(hits) - 5} more — run: brain open {relpath(p)})"))
                break
            line = line if len(line) <= 120 else line[:119] + "…"
            highlight = pat.sub(lambda m: yellow(m.group(0)), line)
            print(f"  :{i}  {highlight}")
            shown += 1
        # Back-references
        refs = backrefs(p)
        if refs:
            print(dim("  used by:"))
            for rp, rl, rline in refs:
                short = (rline[:90] + "...") if len(rline) > 90 else rline
                print(f"    {blue(relpath(rp))}:{rl}  {dim(short)}")
    if total == 0:
        print(dim(f"(no '{query}' matches in topic '{topic}')"))
        print(dim(f"Try broader search: `brain find {query}` or command-only search: `brain cmd {query}`"))
    else:
        print(dim(f"\n{total} match(es) in {topic}"))
    return 0


def cmd_list(argv: list[str]) -> int:
    which = argv[0] if argv else "all"
    cats = ("tools", "exploits", "privesc", "playbooks", "techniques", "payloads", "writeups") if which == "all" else (which,)
    for cat in cats:
        if cat not in DIRS:
            print(red(f"Unknown category: {cat}")); return 2
        print(bold(f"\n== {cat} =="))
        for p in iter_category(cat):
            print(f"  {cyan(p.stem)}  {dim('('+relpath(p)+')')}")
    return 0


def cmd_search(argv: list[str], code_only: bool = False) -> int:
    if not argv:
        print(red("usage: brain search [category|commands] <query>")); return 2
    
    target_cat = None
    cat_aliases = {
        "tools": "tools", "tool": "tools", "herramientas": "tools", "herramienta": "tools",
        "exploits": "exploits", "exploit": "exploits",
        "privesc": "privesc", "escalation": "privesc", "privilegios": "privesc",
        "playbooks": "playbooks", "playbook": "playbooks",
        "techniques": "techniques", "technique": "techniques",
        "payloads": "payloads", "payload": "payloads",
        "writeups": "writeups", "writeup": "writeups",
    }
    cmd_aliases = {"commands", "command", "cmd", "comandos", "comando"}
    
    while argv and len(argv) > 1:
        first = argv[0].lower()
        if first in cmd_aliases:
            code_only = True
            argv = argv[1:]
        elif first in cat_aliases:
            target_cat = cat_aliases[first]
            argv = argv[1:]
        else:
            break
            
    query = " ".join(argv)
    pat = re.compile(re.escape(query), re.IGNORECASE)
    total = 0
    for cat, p in iter_all():
        if target_cat and cat != target_cat:
            continue
        hits = _grep_file(p, pat, code_only=code_only)
        if not hits:
            continue
        shown = 0
        for i, line in hits:
            total += 1
            if shown >= 5:
                print(dim(f"  ... (+{len(hits) - 5} more in {relpath(p)})"))
                break
            line = line if len(line) <= 120 else line[:119] + "…"
            highlight = pat.sub(lambda m: yellow(m.group(0)), line)
            print(f"{green(relpath(p))}:{i}  {highlight}")
            shown += 1
    if total == 0:
        scope = target_cat if target_cat else "all files"
        kind = "commands" if code_only else "text"
        print(dim(f"(no {kind} matches for '{query}' in {scope})"))
    else:
        print(dim(f"\n{total} match(es)"))
    return 0


def _resolve_file(cat: str, name: str, quiet: bool = False) -> Path | None:
    name_low = name.lower()
    exact, partials = [], []
    for p in iter_category(cat):
        stem = p.stem.lower()
        if stem == name_low:
            exact.append(p)
        elif name_low in stem:
            partials.append(p)
    if exact:
        return exact[0]
    if len(partials) == 1:
        return partials[0]
    if partials:
        if not quiet:
            print(yellow(f"Ambiguous '{name}'. Candidates:"))
            for p in partials:
                print(f"  {relpath(p)}")
        return None
    if not quiet:
        print(red(f"No {cat[:-1]} matching '{name}'."))
    return None


def cmd_show(cat: str, argv: list[str]) -> int:
    if not argv:
        return cmd_list([cat])
    p = _resolve_file(cat, argv[0])
    if not p:
        return 1
    print(read_text(p))
    # Plus back-references at the bottom for reusable notes
    if cat in ("tools", "exploits", "payloads"):
        refs = backrefs(p)
        if refs:
            print(bold(f"\n== Referenced by =="))
            for rp, rl, _ in refs:
                print(f"  {blue(relpath(rp))}:{rl}")
    return 0


def cmd_used_on(argv: list[str]) -> int:
    if not argv:
        print(red("usage: brain used-on <Machine>")); return 2
    machine = " ".join(argv)
    pat = re.compile(r"Used on:.*" + re.escape(machine), re.IGNORECASE)
    hits = 0
    for cat, p in iter_all():
        text = read_text(p)
        if pat.search(text):
            hits += 1
            print(f"  {cyan(relpath(p))}")
    if not hits:
        print(dim(f"(no notes tagged '{machine}')"))
    return 0


def cmd_backrefs(argv: list[str]) -> int:
    if not argv:
        print(red("usage: brain backrefs <note-name-or-path>")); return 2
    target = argv[0]
    # Try to resolve by stem across reusable notes
    p: Path | None = None
    for cat in ("tools", "exploits", "privesc", "playbooks", "techniques", "payloads"):
        p = _resolve_file(cat, target, quiet=True)
        if p:
            break
    if not p:
        cand = ROOT / target
        if cand.exists():
            p = cand
    if not p:
        print(red(f"Cannot resolve '{target}'.")); return 1
    refs = backrefs(p)
    print(bold(f"Back-references to {relpath(p)}"))
    if not refs:
        print(dim("  (none)")); return 0
    for rp, rl, line in refs:
        short = (line[:100] + "...") if len(line) > 100 else line
        print(f"  {blue(relpath(rp))}:{rl}  {dim(short)}")
    return 0


def cmd_open(argv: list[str]) -> int:
    if not argv:
        print(red("usage: brain open <path>")); return 2
    p = Path(argv[0])
    if not p.is_absolute():
        p = ROOT / p
    if not p.exists():
        print(red(f"not found: {p}")); return 1
    editor = os.environ.get("EDITOR") or os.environ.get("VISUAL")
    if editor:
        return subprocess.call([editor, str(p)])
    print(read_text(p))
    return 0


# ---- Dispatch ----

FIXED_COMMANDS = {
    "stats":    cmd_stats,
    "topics":   cmd_topics,
    "temas":    cmd_topics,
    "guide":    cmd_guide,
    "guia":     cmd_guide,
    "ayuda":    cmd_guide,
    "quick":    cmd_guide,
    "quickstart": cmd_guide,
    "find":     lambda a: cmd_search(a, code_only=False),
    "buscar":   lambda a: cmd_search(a, code_only=False),
    "search":   lambda a: cmd_search(a, code_only=False),
    "cmd":      lambda a: cmd_search(a, code_only=True),
    "comandos": lambda a: cmd_search(a, code_only=True),
    "list":     cmd_list,
    "lista":    cmd_list,
    "tool":     lambda a: cmd_show("tools", a),
    "tools":    lambda a: cmd_show("tools", a),
    "herramienta": lambda a: cmd_show("tools", a),
    "herramientas": lambda a: cmd_show("tools", a),
    "exploit":  lambda a: cmd_show("exploits", a),
    "exploits": lambda a: cmd_show("exploits", a),
    "payload":  lambda a: cmd_show("payloads", a),
    "payloads": lambda a: cmd_show("payloads", a),
    "playbook": lambda a: cmd_show("playbooks", a),
    "playbooks": lambda a: cmd_show("playbooks", a),
    "technique": lambda a: cmd_show("techniques", a),
    "techniques": lambda a: cmd_show("techniques", a),
    "writeup":  lambda a: cmd_show("writeups", a),
    "writeups": lambda a: cmd_show("writeups", a),
    "used-on":  cmd_used_on,
    "backrefs": cmd_backrefs,
    "open":     cmd_open,
    "help":     lambda a: (print(__doc__) or 0),
    "-h":       lambda a: (print(__doc__) or 0),
    "--help":   lambda a: (print(__doc__) or 0),
}


def main(argv: list[str]) -> int:
    argv = configure_color(argv)
    if not argv:
        print(__doc__); return 0
    cmd, rest = argv[0], argv[1:]
    # Topic dispatch takes precedence when `exploit` is followed by a keyword
    # that does NOT match an existing exploit file name.
    key = TOPIC_ALIASES.get(cmd, cmd)
    if key in TOPICS:
        # Special-case: `brain exploit <name>` where <name> is a known exploit
        # file → behave like the old show-file command.
        if cmd in ("exploit", "exploits") and rest:
            found = _find_exact("exploits", rest[0])
            if found:
                return cmd_show("exploits", rest)
        if cmd in ("tool", "tools") and rest:
            found = _find_exact("tools", rest[0])
            if found:
                return cmd_show("tools", rest)
        if cmd in ("payload", "payloads") and rest:
            found = _find_exact("payloads", rest[0])
            if found:
                return cmd_show("payloads", rest)
        if cmd in ("playbook", "playbooks") and rest:
            found = _find_exact("playbooks", rest[0])
            if found:
                return cmd_show("playbooks", rest)
        if cmd in ("technique", "techniques") and rest:
            found = _find_exact("techniques", rest[0])
            if found:
                return cmd_show("techniques", rest)
        if cmd in ("privesc",) and rest:
            found = _find_exact("privesc", rest[0])
            if found:
                return cmd_show("privesc", rest)
        return cmd_topic(key, rest)
    if cmd in FIXED_COMMANDS:
        return FIXED_COMMANDS[cmd](rest) or 0
    print(red(f"Unknown command or topic: {cmd}\n"))
    print(dim("Try `brain guide` for beginner examples, `brain topics` for scopes, or `brain find <keyword>` for broad search.\n"))
    print(__doc__)
    return 2


def _find_exact(cat: str, name: str) -> Path | None:
    n = name.lower()
    for p in iter_category(cat):
        if p.stem.lower() == n:
            return p
    return None


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except KeyboardInterrupt:
        sys.exit(130)
