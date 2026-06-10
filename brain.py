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
                                 Lines below `Command:`, `CLI:` or
                                 `<!-- brain:command -->` also count.

  brain tool      [name]                Show a tool note (or list all).
  brain tool      <name> search <kw>    Search keyword inside a specific tool note.
  brain exploit   [name]                Show an exploit note (or list all).
  brain exploit   <name> search <kw>    Search keyword inside a specific exploit note.
  brain technique <name> search <kw>    Search keyword inside a technique note.
  brain writeup   <name> search <kw>    Search keyword inside a writeup.
  brain payload   [name]                Show a payload/snippet note (or list all).
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
  brain tool metasploit search route          # search 'route' inside metasploit.md
  brain exploit eternalblue search nmap       # search inside a specific exploit note
  brain writeup Billing search meterpreter    # search inside a specific writeup
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


SEARCH_PREVIEW_LIMIT = 8


def _safe_regex(query: str) -> re.Pattern:
    return re.compile(re.escape(query), re.IGNORECASE)


def _shorten(text: str, width: int = 140) -> str:
    return text if len(text) <= width else text[: width - 1] + "…"


def _separator(label: str = "") -> str:
    width = 78
    if not label:
        return dim("─" * width)
    raw = f" {label} "
    return dim("─" * 2) + bold(raw) + dim("─" * max(2, width - len(raw) - 2))


def _highlight(line: str, pat: re.Pattern) -> str:
    return pat.sub(lambda m: yellow(bold(m.group(0))), line)


def _strip_command_wrappers(line: str) -> str:
    stripped = line.strip()
    for prompt in ("$ ", "# ", "> ", "PS> "):
        if stripped.startswith(prompt):
            stripped = stripped[len(prompt):].lstrip()

    wrappers = {"sudo", "proxychains", "proxychains4", "rlwrap", "winpty", "xargs", "env"}
    parts = stripped.split()
    while parts and parts[0].lower() in wrappers:
        parts = parts[1:]
    while parts and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", parts[0]):
        parts = parts[1:]
    return " ".join(parts)


def _command_token(line: str) -> str | None:
    stripped = _strip_command_wrappers(line)
    if not stripped or stripped.startswith(("#", "//", "/*", "*", "|", "}", "]", ")")):
        return None
    token = stripped.split(None, 1)[0].strip("\"'`")
    token = Path(token).name if "/" in token or "\\" in token else token
    token = token.lower()
    if not re.match(r"^[a-z0-9_.+-]{2,}$", token):
        return None
    if "." in token and not token.endswith((".py", ".ps1", ".sh", ".exe", ".php", ".rb", ".pl")):
        return None
    return token


def command_prefixes() -> set[str]:
    """Build command tokens from repository tool notes instead of hand-maintaining them."""
    global _COMMAND_PREFIXES
    if _COMMAND_PREFIXES is not None:
        return _COMMAND_PREFIXES

    prefixes: set[str] = set()
    for p in iter_category("tools"):
        prefixes.add(p.stem.lower())

        in_code = False
        for line in read_text(p).splitlines():
            if line.lstrip().startswith("```"):
                in_code = not in_code
                continue
            if not in_code:
                continue
            token = _command_token(line)
            if token:
                prefixes.add(token)

    prefixes.update({"bash", "sh", "python", "python3", "powershell", "cmd", "pwsh"})
    _COMMAND_PREFIXES = prefixes
    return prefixes


def _looks_like_command_line(line: str) -> bool:
    stripped = _strip_command_wrappers(line)
    if not stripped:
        return False
    if stripped.startswith(("./", "../", "/")):
        return True
    token = _command_token(stripped)
    return bool(token and token in command_prefixes())


def _format_hit_line(lineno: int, line: str, pat: re.Pattern, *, command_hint: bool = False, platform: str | None = None) -> str:
    shortened = _shorten(line.rstrip())
    rendered = _highlight(shortened, pat)
    
    # Colorear según plataforma si es un comando
    if platform:
        platform_color_map = {
            "linux": cyan,
            "windows": red,
            "cross-platform": green,
            "docker": blue,
            "sql": yellow,
            "http": green,
            "python": yellow,
        }
        color_func = platform_color_map.get(platform, cyan)
        badge = f"[{platform}]"
        rendered = f"{color_func(badge)} {color_func(rendered)}"
    elif command_hint or _looks_like_command_line(line):
        rendered = cyan(rendered)
    
    return f"  {dim(str(lineno)).rjust(5)}  {rendered}"


def print_note(p: Path) -> None:
    in_code = False
    for line in read_text(p).splitlines():
        stripped = line.lstrip()
        if stripped.startswith("```"):
            in_code = not in_code
            print(dim(line))
        elif in_code:
            print(cyan(line))
        elif stripped.startswith("#"):
            print(bold(line))
        elif "Used on:" in line:
            print(green(line))
        else:
            print(line)


def _is_within_root(path: Path) -> bool:
    try:
        path.resolve().relative_to(ROOT)
        return True
    except ValueError:
        return False


_BACKREF_INDEX: dict[str, list[tuple[Path, int, str]]] | None = None
_COMMAND_PREFIXES: set[str] | None = None


COMMAND_HINT_MARKERS = (
    "<!-- brain:command -->",
    "<!-- brain:commands -->",
    "[COMMAND]",
    "[COMMANDS]",
    "Command:",
    "Commands:",
    "CLI:",
)

CATEGORY_COMMANDS = {
    "tool": "tools", "tools": "tools",
    "exploit": "exploits", "exploits": "exploits",
    "payload": "payloads", "payloads": "payloads",
    "playbook": "playbooks", "playbooks": "playbooks",
    "technique": "techniques", "techniques": "techniques",
    "privesc": "privesc",
    "writeup": "writeups", "writeups": "writeups",
}

SEARCH_CATEGORY_ALIASES = {
    **CATEGORY_COMMANDS,
    "escalation": "privesc",
}

COMMAND_SEARCH_ALIASES = {"commands", "command", "cmd"}


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
                  "onesixtyone", "snmpwalk", "snmpset", "nikto", "bloodhound", "find", "grep",
                  "httrack"],
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
                     "suid-find-escape", "incron-module-hijacking",
                     "invoke-expression-file-injection", "mcafee-madb-credential-recovery",
                     "addself-privesc"],
    },
    "shells": {
        "desc": "Reverse-shell one-liners and listener patterns",
        "tools": ["netcat", "socat", "ssh", "sshpass", "evil-winrm", "impacket", "metasploit", "msfvenom",
                  "meterpreter", "chisel", "plink"],
        "exploits": [],
        "all_payloads": True,
        "keywords": ["bash -i", "/dev/tcp/", "nc -lvnp", "pty.spawn",
                     "socat", "mkfifo", "stty raw -echo", "powershell -enc"],
    },
    "payloads": {
        "desc": "Reusable payload snippets, webshells and shell stabilization",
        "tools": ["netcat", "socat", "ssh", "msfvenom", "meterpreter"],
        "exploits": [],
        "all_payloads": True,
    },
    "creds": {
        "desc": "Credential hunting, cracking, reuse",
        "tools": ["hashcat", "john", "gpg", "tcpdump", "strings", "responder",
                  "mimikatz", "hydra", "ldap-utils", "mcafee-sitelist-pwd-decrypt"],
        "exploits": ["bash-history-credentials", "env-variable-enum",
                     "ntlm-capture-crack", "pgp-key-cracking",
                     "password-spraying", "kerberos-roasting", "shadow-credentials",
                     "tcpdump-credential-sniffing", "binary-credential-hunting",
                     "systemd-service-credentials", "base64-encoded-credentials",
                     "mimikatz-sam-pth", "windows-sam-hive-dump",
                     "wordpress-wp-config-credentials", "firefox-credential-extraction",
                     "jenkins-http-form-bruteforce", "ldap-passback-attack", "asreproast",
                     "pxe-boot-credential-scraping", "mcafee-madb-credential-recovery"],
    },
    "ad": {
        "desc": "Active Directory / Kerberos / SMB / LDAP",
        "tools": ["netexec", "impacket", "kerbrute", "smbclient", "evil-winrm",
                  "dnstool", "responder", "bloodhound", "mimikatz", "xfreerdp",
                  "hydra", "ldap-utils", "runas", "powerpxe", "powerview"],
        "exploits": ["adidns-poisoning", "kerberos-roasting", "password-spraying",
                     "smb-anonymous-enum", "smb-enumeration", "shadow-credentials",
                     "rid-brute-enumeration", "mssql-", "ntlm-capture-crack",
                     "windows-enumeration", "smb-write-iis-execution",
                     "base64-encoded-credentials", "mimikatz-sam-pth",
                     "windows-admin-stabilization", "windows-sam-hive-dump",
                     "ldap-passback-attack", "asreproast",
                     "xmpp-spark-ntlm-leak", "invoke-expression-file-injection",
                     "pxe-boot-credential-scraping", "addself-privesc"],
    },
    "web": {
        "desc": "Web / HTTP exploitation",
        "tools": ["curl", "sqlmap", "ffuf", "gobuster", "feroxbuster", "wget",
                  "whatweb", "exiftool", "gittools", "wpscan", "nuclei", "padre",
                  "metasploit", "msfvenom", "nikto", "httrack"],
        "exploits": ["sweetrice-media-center-rce", "magnusbilling-rce",
                     "cacti-rce", "apache-cxf-xop-lfi", "oscommerce-installer-rce",
                     "backup-file-exposure", "lfi-php-parameter",
                     "env-file-exposure", "url-param-command-injection",
                     "codiad-rce", "mailhog-password-reset",
                     "hoverfly-middleware-rce", "motioneye-config-injection",
                     "wcf-soap-injection", "flowise-mcp-rce", "mcp-api-injection",
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
                     "freepbx-unauth-sqli-rce",
                     "xmpp-spark-ntlm-leak", "youtube-dl-command-injection",
                     "nodejs-module-upload-rce"],
    },
    "webdav": {
        "desc": "WebDAV enumeration and exploitation",
        "tools": ["cadaver", "davtest"],
        "exploits": ["webdav-upload-rce"],
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
        "exploits": ["sql-union-injection", "sql-injection", "sqli",
                     "freepbx-extractvalue-sqli"],
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
        "exploits": ["url-param-command-injection", "cacti-rce",
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
                     "joomla-template-editor-webshell", "nodejs-eval-rce",
                     "asterisk-ami-command-execution",
                     "freepbx-unauth-sqli-rce", "invoke-expression-file-injection",
                     "youtube-dl-command-injection", "nodejs-module-upload-rce"],
    },
    "reversing": {
        "desc": "Binary reverse engineering (SUID, custom binaries)",
        "tools": ["strings", "ltrace", "objdump", "pycdc", "apktool", "jadx"],
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
                     "chisel-pivoting", "powershell-empire-hop-listener", "pivoting-tunnelling",
                     "meterpreter-pivoting"],
    },
}

# Aliases
TOPIC_ALIASES = {
    "enum": "enumeration", "enumeration": "enumeration",
    "recon": "recon", "reconnaissance": "recon",
    "escalation": "privesc", "shell": "shells", "reverse-shell": "shells",
    "payload": "payloads", "payloads": "payloads",
    "pivoting": "pivot", "tunnel": "pivot",
    "active-directory": "ad", "kerberos": "ad",
    "cross-site-scripting": "xss",
    "steganography": "stego", "credentials": "creds",
    "password": "creds", "passwords": "creds", "http": "web",
    "reverse": "reversing", "binary": "reversing", "re": "reversing",
    "docker": "container", "containers": "container", "k8s": "container",
    "db": "database", "database": "database",
    "mongodb": "database", "sqlite": "database", "nosql": "database",
    "padding": "crypto", "oracle": "crypto", "weak-crypto": "crypto",
    "sql": "sqli",
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
    platform: str | None = None  # linux, windows, cross-platform, docker, sql, http, python


def scan_markdown(p: Path) -> list[LineHit]:
    text = read_text(p)
    if not text:
        return []
    lines: list[LineHit] = []
    in_code = False
    command_hint_lines = 0
    current_platform = None
    platform_pattern = re.compile(r'<!--\s*cmd:\s*(linux|windows|cross-platform|docker|sql|http|python)\s*-->')
    
    for i, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        
        # Detectar marcador de plataforma
        platform_match = platform_pattern.search(stripped)
        if platform_match:
            current_platform = platform_match.group(1)
            lines.append(LineHit(i, line.rstrip(), False, platform=current_platform))
            continue
        
        if stripped.startswith("```"):
            in_code = not in_code
            command_hint_lines = 0
            # Limpiar plataforma cuando termina el bloque de código
            if not in_code:
                current_platform = None
            continue
        if any(marker.lower() in stripped.lower() for marker in COMMAND_HINT_MARKERS):
            command_hint_lines = 2
            lines.append(LineHit(i, line.rstrip(), in_code, platform=current_platform if in_code else None))
            continue
        is_command_hint = command_hint_lines > 0 and bool(stripped)
        lines.append(LineHit(i, line.rstrip(), in_code or is_command_hint, platform=current_platform if (in_code or is_command_hint) else None))
        if command_hint_lines > 0 and stripped:
            command_hint_lines -= 1
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

def _build_backref_index() -> dict[str, list[tuple[Path, int, str]]]:
    note_names = {
        p.name
        for cat in ("tools", "exploits", "privesc", "playbooks", "techniques", "payloads")
        for p in iter_category(cat)
    }
    index: dict[str, list[tuple[Path, int, str]]] = {name: [] for name in note_names}
    for p in iter_category("writeups"):
        for i, line in enumerate(read_text(p).splitlines(), 1):
            stripped = line.strip()
            for name in note_names:
                if name in line:
                    index[name].append((p, i, stripped))
    return index


def backrefs(target: Path) -> list[tuple[Path, int, str]]:
    global _BACKREF_INDEX
    if _BACKREF_INDEX is None:
        _BACKREF_INDEX = _build_backref_index()
    return _BACKREF_INDEX.get(target.name, [])


# ---- Search primitives ----

def _grep_file(p: Path, pat: re.Pattern, code_only: bool = False) -> list[tuple[int, str, bool, str | None]]:
    # Plain-text payload lists: every line is a payload — treat as code-only content
    if p.suffix == ".txt":
        hits = []
        for i, line in enumerate(read_text(p).splitlines(), 1):
            line = line.rstrip()
            if line and pat.search(line):
                hits.append((i, line, True, None))
        return hits
    hits: list[tuple[int, str, bool, str | None]] = []
    for hit in scan_markdown(p):
        if code_only and not hit.in_code:
            continue
        if pat.search(hit.text):
            hits.append((hit.lineno, hit.text, hit.in_code, hit.platform))
    hits.sort(key=lambda x: (not x[2], x[0]))
    return hits


def _looks_command_like(query: str) -> bool:
    q = query.lower()
    if any(marker in q for marker in (" -", "--", "/", "\\", "$", "|", ">", "<", "=", "http://", "https://")):
        return True
    token = _command_token(q)
    return bool(token and token in command_prefixes())


def _topic_hits(p: Path, pat: re.Pattern, query: str) -> list[tuple[int, str, str | None]]:
    scanned = scan_markdown(p)
    if not scanned:
        return []

    code_hits = [(h.lineno, h.text, h.platform) for h in scanned if h.in_code and pat.search(h.text)]
    prose_hits = [(h.lineno, h.text, None) for h in scanned if not h.in_code and pat.search(h.text)]

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
        for i, line, platform in hits:
            if shown >= 5:
                print(dim(f"  ... (+{len(hits) - 5} more — run: brain open {relpath(p)})"))
                break
            line = line if len(line) <= 120 else line[:119] + "…"
            highlight = pat.sub(lambda m: yellow(m.group(0)), line)
            if platform:
                platform_color_map = {
                    "linux": cyan,
                    "windows": red,
                    "cross-platform": green,
                    "docker": blue,
                    "sql": yellow,
                    "http": green,
                    "python": yellow,
                }
                color_func = platform_color_map.get(platform, cyan)
                badge = f"[{platform}]"
                highlight = f"{color_func(badge)} {highlight}"
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

    while argv and len(argv) > 1:
        first = argv[0].lower()
        if first in COMMAND_SEARCH_ALIASES:
            code_only = True
            argv = argv[1:]
        elif first in SEARCH_CATEGORY_ALIASES:
            target_cat = SEARCH_CATEGORY_ALIASES[first]
            argv = argv[1:]
        else:
            break
            
    query = " ".join(argv).strip()
    if not query:
        print(red("usage: brain search [category|commands] <query>")); return 2

    pat = _safe_regex(query)
    total = 0
    files_with_hits = 0
    for cat, p in iter_all():
        if target_cat and cat != target_cat:
            continue
        hits = _grep_file(p, pat, code_only=code_only)
        if not hits:
            continue
        files_with_hits += 1
        total += len(hits)
        header = f"{relpath(p)}  ({len(hits)} match{'es' if len(hits) != 1 else ''})"
        print()
        print(_separator(header))
        shown = 0
        for i, line, in_code, platform in hits:
            if shown >= SEARCH_PREVIEW_LIMIT:
                print(dim(f"  ... (+{len(hits) - SEARCH_PREVIEW_LIMIT} more - run: brain open {relpath(p)})"))
                break
            print(_format_hit_line(i, line, pat, command_hint=code_only, platform=platform))
            shown += 1
        if cat in ("tools", "exploits", "privesc", "playbooks", "techniques", "payloads"):
            refs = backrefs(p)
            if refs:
                print(dim("  referenced by:"))
                for rp, rl, rline in refs[:5]:
                    print(f"    {blue(relpath(rp))}:{rl}  {dim(_shorten(rline, 100))}")
                if len(refs) > 5:
                    print(dim(f"    ... (+{len(refs) - 5} more - run: brain backrefs {p.stem})"))
    if total == 0:
        scope = target_cat if target_cat else "all files"
        kind = "commands" if code_only else "text"
        print(dim(f"(no {kind} matches for '{query}' in {scope})"))
    else:
        print(dim(f"\n{total} match(es) across {files_with_hits} file(s)"))
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


def _cmd_file_search(p: Path, query: str) -> int:
    """Grep a single file for query with colored highlights."""
    query = query.strip()
    if not query:
        print(red("usage: brain <category> <name> search <query>")); return 2
    pat = _safe_regex(query)
    hits = _grep_file(p, pat, code_only=False)
    if not hits:
        print(dim(f"(no matches for '{query}' in {relpath(p)})"))
        print(dim(f"Try broader: brain search {query}"))
        return 1
    print(_separator(f"{relpath(p)}  ({len(hits)} match{'es' if len(hits) != 1 else ''} for {query})"))
    for lineno, line, in_code, platform in hits:
        print(_format_hit_line(lineno, line, pat, platform=platform))
    return 0


def cmd_category_search(cat: str, argv: list[str]) -> int:
    if not argv:
        return cmd_list([cat])
    return cmd_search([cat, *argv])


def cmd_show(cat: str, argv: list[str]) -> int:
    if not argv:
        return cmd_list([cat])
    # Inline search: `brain tool metasploit search route`
    # Works for every category: tools, exploits, techniques, writeups, privesc, etc.
    if len(argv) >= 3 and argv[1].lower() == "search":
        p = _resolve_file(cat, argv[0])
        if not p:
            return 1
        query = " ".join(argv[2:])
        return _cmd_file_search(p, query)
    p = _resolve_file(cat, argv[0])
    if not p:
        return 1
    print_note(p)
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
        cand = Path(target)
        if not cand.is_absolute():
            cand = ROOT / cand
        cand = cand.resolve()
        if cand.exists() and cand.is_file() and _is_within_root(cand):
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
    p = p.resolve()
    if not _is_within_root(p):
        print(red("refusing to open a path outside this repository")); return 1
    if not p.exists():
        print(red(f"not found: {p}")); return 1
    if not p.is_file():
        print(red(f"not a file: {p}")); return 1
    editor = os.environ.get("EDITOR") or os.environ.get("VISUAL")
    if editor:
        return subprocess.call([editor, str(p)])
    print_note(p)
    return 0


# ---- Dispatch ----

FIXED_COMMANDS = {
    "stats":    cmd_stats,
    "topics":   cmd_topics,
    "temas":    cmd_topics,
    "guide":    cmd_guide,
    "guia":     cmd_guide,
    "ayuda":    cmd_guide,
    "find":     lambda a: cmd_search(a, code_only=False),
    "buscar":   lambda a: cmd_search(a, code_only=False),
    "search":   lambda a: cmd_search(a, code_only=False),
    "cmd":      lambda a: cmd_search(a, code_only=True),
    "list":     cmd_list,
    "used-on":  cmd_used_on,
    "backrefs": cmd_backrefs,
    "open":     cmd_open,
    "help":     lambda a: (print(__doc__) or 0),
}


def main(argv: list[str]) -> int:
    argv = configure_color(argv)
    if not argv:
        print(__doc__); return 0
    cmd, rest = argv[0], argv[1:]

    # Map category command names to their directory categories
    _CMD_CAT: dict[str, str] = {
        "exploit": "exploits", "exploits": "exploits",
        "tool": "tools", "tools": "tools",
        "payload": "payloads", "payloads": "payloads",
        "playbook": "playbooks", "playbooks": "playbooks",
        "technique": "techniques", "techniques": "techniques",
        "privesc": "privesc",
        "writeup": "writeups", "writeups": "writeups",
    }

    key = TOPIC_ALIASES.get(cmd, cmd)

    # Category commands (tool, exploit, technique, writeup …) take priority when
    # followed by a known or partial file name, including inline `search` sub-command.
    if cmd in _CMD_CAT and rest:
        cat = _CMD_CAT[cmd]
        # `brain tool metasploit search route`  →  grep inside that file
        if len(rest) >= 3 and rest[1].lower() == "search":
            return cmd_show(cat, rest)
        # `brain tool metasploit`  →  show the file (exact or partial match)
        found = _resolve_file(cat, rest[0], quiet=True)
        if found:
            return cmd_show(cat, rest)
        # No file match → fall through to topic search (e.g. `brain web curl`)

    # Topic dispatch: `brain web curl`, `brain privesc sudo`, …
    if key in TOPICS:
        return cmd_topic(key, rest)

    # Fixed top-level commands: search, find, cmd, list, used-on, …
    if cmd in FIXED_COMMANDS:
        return FIXED_COMMANDS[cmd](rest) or 0

    print(red(f"Unknown command or topic: {cmd}\n"))
    print(dim("Try `brain guide` for beginner examples, `brain topics` for scopes, or `brain find <keyword>` for broad search.\n"))
    print(__doc__)
    return 2

if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except KeyboardInterrupt:
        sys.exit(130)
