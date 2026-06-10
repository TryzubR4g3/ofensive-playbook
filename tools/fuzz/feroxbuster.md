# feroxbuster

## Internal / Decryptify Commands

<!-- cmd: linux -->
```bash
feroxbuster -u http://internal.thm -w /usr/share/wordlists/seclists/Discovery/Web-Content/DirBuster-2007_directory-list-2.3-medium.txt
feroxbuster -u http://$TARGET:1337 -w /usr/share/wordlists/seclists/Discovery/Web-Content/DirBuster-2007_directory-list-2.3-medium.txt --dont-scan locale
```
Used on: **Internal**, **Decryptify**

discovered WordPress content and exposed Decryptify web paths.

Fast, recursive web content discovery tool written in Rust. Used for directory and file brute-forcing against HTTP targets, including multi-port web applications.

## Commands Used

### Recursive directory brute-force (standard wordlist)
<!-- cmd: linux -->
```bash
feroxbuster -u http://team.thm/ \
  -w /usr/share/seclists/Discovery/Web-Content/DirBuster-2007_directory-list-2.3-big.txt
```
Used on: **Team**

### Directory brute-force on non-standard port
<!-- cmd: linux -->
```bash
feroxbuster -u http://TARGET_IP:62337/ \
  -w /usr/share/seclists/Discovery/Web-Content/big.txt
```
Used on: **IDE**

Non-standard ports (e.g. `62337`) must be included explicitly in the URL

### Recursive deep enumeration with extension sweep
<!-- cmd: linux -->
```bash
feroxbuster \
  -u http://variatype.htb \
  -w /usr/share/wordlists/seclists/Discovery/Web-Content/raft-medium-directories-lowercase.txt \
  -x php,py,ttf,designspace,git,log,json,txt,html,bak,old,backup,swp,sql,db,config \
  -d 4 -t 80 \
  -C 404,403 \
  -s 200,204,301,302,307 \
  --redirects \
  --force-recursion \
  -o ferox_completo.txt
```
Used on: **VariaType**

`-x` — comma-separated extensions appended to each word
- `-d 4` — recurse 4 levels deep
- `-C 404,403` — collect-and-skip these codes (filter)
- `-s 200,...` — only emit these status codes
- `--force-recursion` — recurse into 200s even when they look like files
- `-o file.txt` — persist results so a long run survives a disconnect

### Brute-force a non-default web port (Apache 3333)
<!-- cmd: linux -->
```bash
feroxbuster -u http://$TARGET:3333 -w /usr/share/wordlists/seclists/Discovery/Web-Content/big.txt
```
Used on: **vulnversity**

found `internal/uploads/` upload directory.

### Brute-force IIS root with Recruit-style wordlist
<!-- cmd: linux -->
```bash
feroxbuster -u http://$TARGET -w /usr/share/wordlists/seclists/Discovery/Web-Content/DirBuster-2007_directory-list-2.3-big.txt
```
Used on: **Recruit**

discovered `/phpmyadmin/` plus the entry-point `file.php`.



### Brute-force multiple HTTP ports on the same target
<!-- cmd: linux -->
```bash
feroxbuster -u http://$TARGET:8080 -w /usr/share/seclists/Discovery/Web-Content/big.txt
feroxbuster -u http://$TARGET:8082 -w /usr/share/seclists/Discovery/Web-Content/big.txt
```
Used on: **coldvvars**

mapped the web apps on both non-standard ports before deeper `/dev` fuzzing.

### Multi-extension sweep on a non-standard port with status-code allowlist
<!-- cmd: linux -->
```bash
feroxbuster -u http://10.200.30.101:8002 \
  -w /usr/share/wordlists/dirb/common.txt \
  -x php,js,env,conf,txt,html,json,config,bak,sql,db \
  -t 50 \
  -d 3 \
  --status-codes 200,201,301,302,403,405,500 \
  -o ferox-8002.txt
```
Used on: **Bandit**

enumerated the Hadoop service on port 8002; `-x` sweep catches config and backup leaks; `--status-codes` allowlist surfaces 403/500 that indicate interesting paths even when access is denied.

- `--status-codes` — emit only these codes (allowlist, opposite of `-C`/`--filter-status`)
- `-d 3` — recurse three levels to catch nested API routes
- `-o` — persist output for later grep/review

### Brute-force Next.js application with status-code filter
<!-- cmd: linux -->
```bash
feroxbuster -u http://$TARGET:3000 \
  -w /usr/share/seclists/Discovery/Web-Content/DirBuster-2007_directory-list-2.3-medium.txt \
  --status-codes 200 301
```
Used on: **Reactor**

filtered status codes to bypass Next.js 400 responses on unknown endpoints.

### Deep web fuzzing with extensions
<!-- cmd: linux -->
```bash
feroxbuster -u http://flower.shop \
  -w /usr/share/wordlists/dirb/common.txt \
  -x js,html,php \
  -d 5
```
Used on: **flower**

enumerated web content before testing the search endpoint for SQL injection.
