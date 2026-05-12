# feroxbuster

## Internal / Decryptify Commands

```bash
feroxbuster -u http://internal.thm -w /usr/share/wordlists/seclists/Discovery/Web-Content/DirBuster-2007_directory-list-2.3-medium.txt
feroxbuster -u http://$TARGET:1337 -w /usr/share/wordlists/seclists/Discovery/Web-Content/DirBuster-2007_directory-list-2.3-medium.txt --dont-scan locale
```
Used on: **Internal**, **Decryptify** - discovered WordPress content and exposed Decryptify web paths.

Fast, recursive web content discovery tool written in Rust. Used for directory and file brute-forcing against HTTP targets, including multi-port web applications.

## Commands Used

### Recursive directory brute-force (standard wordlist)
```bash
feroxbuster -u http://team.thm/ \
  -w /usr/share/seclists/Discovery/Web-Content/DirBuster-2007_directory-list-2.3-big.txt
```
Used on: **Team**

### Directory brute-force on non-standard port
```bash
feroxbuster -u http://TARGET_IP:62337/ \
  -w /usr/share/seclists/Discovery/Web-Content/big.txt
```
Used on: **IDE**

- Non-standard ports (e.g. `62337`) must be included explicitly in the URL

### Recursive deep enumeration with extension sweep
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

- `-x` â€” comma-separated extensions appended to each word
- `-d 4` â€” recurse 4 levels deep
- `-C 404,403` â€” collect-and-skip these codes (filter)
- `-s 200,...` â€” only emit these status codes
- `--force-recursion` â€” recurse into 200s even when they look like files
- `-o file.txt` â€” persist results so a long run survives a disconnect

### Brute-force a non-default web port (Apache 3333)
```bash
feroxbuster -u http://$TARGET:3333 -w /usr/share/wordlists/seclists/Discovery/Web-Content/big.txt
```
Used on: **vulnversity** â€” found `internal/uploads/` upload directory.

### Brute-force IIS root with Recruit-style wordlist
```bash
feroxbuster -u http://$TARGET -w /usr/share/wordlists/seclists/Discovery/Web-Content/DirBuster-2007_directory-list-2.3-big.txt
```
Used on: **Recruit** â€” discovered `/phpmyadmin/` plus the entry-point `file.php`.


