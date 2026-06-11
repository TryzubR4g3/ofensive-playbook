# Web Discovery Playbook

**Goal**: Identify all web applications, endpoints, and parameters to map the attack surface.

## 1. Subdomain Enumeration
Find all subdomains related to the target.

<!-- cmd: linux -->
```bash
# [USED]
amass enum -active -d <DOMAIN>
```

<!-- cmd: linux -->
```bash
# [USED]
subfinder -d <DOMAIN> -all -recursive
```

## 2. Port Scanning & Web Service Identification
Identify which ports run HTTP/HTTPS.

<!-- cmd: linux -->
```bash
# [USED]
nmap -p- -sV -T4 --min-rate=1000 <IP_OR_DOMAIN>
```

<!-- cmd: linux -->
```bash
# [USED]
httpx -l domains.txt -p 80,443,8080,8443 -title -tech-detect -status-code
```

## 3. Directory and File Brute-Forcing
Discover hidden directories, administrative interfaces, and backup files.

<!-- cmd: linux -->
```bash
# [USED]
ffuf -w /opt/SecLists/Discovery/Web-Content/raft-medium-directories.txt -u http://<TARGET>/FUZZ
```

<!-- cmd: linux -->
```bash
# [USED]
feroxbuster -u http://<TARGET> -w /opt/SecLists/Discovery/Web-Content/raft-large-words.txt -x php,html,bak,txt,zip
```

## 4. Parameter Discovery
Find hidden parameters for injection testing (SQLi, XSS, SSRF).

<!-- cmd: linux -->
```bash
# [USED]
arjun -u http://<TARGET>/page.php -m GET
```

## 5. Spidering and Crawling
Automatically crawl the application to build a sitemap.

<!-- cmd: linux -->
```bash
# [USED]
gospider -s "http://<TARGET>" -c 10 -d 5
```

## Related
- [ffuf.md](../../tools/web/ffuf.md)
- [feroxbuster.md](../../tools/web/feroxbuster.md)
- [httpx.md](../../tools/web/httpx.md)
