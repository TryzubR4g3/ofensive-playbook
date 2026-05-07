# searchsploit

## Wreath Commands

```bash
searchsploit gitstack
searchsploit -m 43777
```
Used on: **Wreath** - found and copied the GitStack 2.3.10 RCE exploit.

Offline CLI for the Exploit-DB database. Given a product + version, returns every public exploit cached locally on Kali / ParrotSec. First-pass reflex after `nmap -sV` or `whatweb` flags a specific version.

## Commands Used

### Version-string search
```bash
searchsploit OpenSSH 7.2p2
# OpenSSH 7.2p2 - Username Enumeration   | linux/remote/40136.py
```
Used on: **LazyAdmin** — flagged CVE-2016-6210 (username enumeration on OpenSSH ≤ 7.2p2). Not exploited in the end, but noted as a viable pivot if brute-forceable.

### General product lookup
```bash
searchsploit <product>
searchsploit "Apache 2.4.18"
searchsploit "SweetRice"
searchsploit "MagnusBilling"
```

### Narrow by type
```bash
searchsploit --exclude="dos|poc" <product>
searchsploit -t <title-keyword>        # title match only
searchsploit -w <product>              # show URLs to Exploit-DB web pages
```

### Show the file contents
```bash
searchsploit -x <path/from/output>
searchsploit -x linux/remote/40136.py
```

### Copy to CWD
```bash
searchsploit -m <path/from/output>
searchsploit -m linux/remote/40136.py
```

### Update the local copy
```bash
searchsploit -u         # git-pulls the latest exploits DB
```

## Tips

- Match Nmap version strings verbatim. A trailing build number (`p2`, `-4ubuntu2.8`) often flips results — try with and without it.
- Combine with `whatweb` on web targets: the banner version goes straight into `searchsploit` before anything else.
- `--cve <CVE-id>` is the reverse lookup when you already know the CVE.

## Related
- [nmap](nmap.md) — feeds the version string
- [whatweb](whatweb.md) — feeds the CMS / framework version
- [metasploit](../exploitation/metasploit.md) — many Exploit-DB entries already have an MSF module — try `search <cve>` there first
