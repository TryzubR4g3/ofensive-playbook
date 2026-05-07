# whatweb

Passive / active HTTP fingerprinter. One HTTP request (or a few) identifies the web server, framework, CMS, JavaScript libraries, server-side language and any redirect target. I run it immediately after `nmap` flags an HTTP service — it's faster and louder than manually browsing headers, and the redirect / title output often tells me where to point `feroxbuster` next.

## Commands Used

### Default scan
```bash
whatweb http://$TARGET/
```
Used on: **Billing** — flagged `Apache[2.4.62]`, `HTTPServer[Debian Linux]`, `RedirectLocation[./mbilling]` — immediately pointed at the MagnusBilling app root.

### Aggression levels
```bash
whatweb -a 1 http://$TARGET/    # passive — single GET, no guessing
whatweb -a 3 http://$TARGET/    # default aggressive — a handful of extra probes
whatweb -a 4 http://$TARGET/    # heavy — active version guessing (loud)
```

### Verbose + full plugin output
```bash
whatweb -v http://$TARGET/
```
Dumps every plugin match (cookies, meta-generators, frameworks) rather than the one-liner summary.

### Batch sweep from a list
```bash
whatweb -i urls.txt --log-brief=whatweb.log
```
Handy when fuzzing has produced a list of live vhosts and you want a one-line fingerprint per entry.

## Typical output to care about

| Field | What to do with it |
|-------|-------------------|
| `HTTPServer` | Pair with Nmap version to search for CVEs |
| `Apache[X.Y.Z]` / `nginx[X.Y.Z]` | Pin exact version — guides CVE / default-config lookup |
| `RedirectLocation` | Tells you the real app root — start fuzzing there, not at `/` |
| `CMS`, `Joomla`, `WordPress`, `Drupal` | Switch to the CMS-specific scanner (wpscan, joomscan) |
| `X-Powered-By` | PHP / ASP.NET / Express clue |
| `Title` | Sometimes leaks branding / product name ? searchsploit |
| `Cookies` | `PHPSESSID`, `ASP.NET_SessionId`, framework cookies (`laravel_session`, `connect.sid`) |

## Pairings

```bash
# After whatweb identifies a framework, go deeper
nikto -h http://$TARGET/
wpscan --url http://$TARGET/ --enumerate u,p
feroxbuster -u http://$TARGET/<redirect_target>/
```

## Related
- [nmap](nmap.md) — precedes whatweb for port/service discovery
- [feroxbuster](../fuzz/feroxbuster.md) — follow the redirect target with directory brute


