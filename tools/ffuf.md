# ffuf

Fast web fuzzer written in Go. Used for directory brute-forcing, API endpoint discovery, virtual host enumeration and parameter fuzzing.

## Commands Used

### API endpoint fuzzing (filter 404 + word-count)
```bash
ffuf -u http://staging.silentium.htb/api/v1/FUZZ \
  -w /usr/share/seclists/Discovery/Web-Content/api-endpoints-res.txt \
  -fc 404 -fw 2
```
Used on: **Silentium**

- `-fc 404` — filter out 404 responses
- `-fw 2` — filter out responses with 2 words

### Directory fuzzing on root
```bash
ffuf -u http://monitorsfour.htb/FUZZ \
  -w /usr/share/wordlists/seclists/Discovery/Web-Content/big.txt
```
Used on: **MonitorsFour**

### API path fuzzing
```bash
ffuf -u http://monitorsfour.htb/api/v1/FUZZ \
  -w /usr/share/wordlists/seclists/Discovery/Web-Content/api/api-endpoints-res.txt
```
Used on: **MonitorsFour**

### Fuzzing with vhost header and size filter
```bash
ffuf -u "http://cacti.monitorsfour.htb/cacti/FUZZ" \
  -H "Host: cacti.monitorsfour.htb" \
  -w /usr/share/wordlists/dirb/common.txt \
  -fs 0 -t 50 -c
```
Used on: **MonitorsFour**

- `-H` — inject custom `Host` header
- `-fs 0` — filter responses of size 0
- `-t 50` — 50 concurrent threads
- `-c` — colored output

### Fuzzing with file extensions
```bash
ffuf -u "http://cacti.monitorsfour.htb/cacti/FUZZ" \
  -H "Host: cacti.monitorsfour.htb" \
  -w /usr/share/wordlists/seclists/Discovery/Web-Content/DirBuster-2007_directory-list-2.3-big.txt \
  -e .php,.txt,.bak,.old,.sql,.env \
  -c -t 50 -fw 1,604
```
Used on: **MonitorsFour**

- `-e` — append extensions to each word
- `-fw 1,604` — filter responses with 1 or 604 words

### LFI parameter fuzzing (filter by word count)
```bash
ffuf -u "http://dev.team.thm/script.php?page=FUZZ" \
  -w /usr/share/wordlists/seclists/Fuzzing/LFI/LFI-Jhaddix.txt \
  -c -t 50 -fw 1,18
```
Used on: **Team**

- `-fw 1,18` — filter out baseline responses with 1 or 18 words

### Backup file extension brute-force
```bash
ffuf -u "http://team.thm/scripts/scriptFUZZ" \
  -w <(echo -e ".bak\n.old\n_backup\n.bkp\n~\n.txt\n.sh\n.orig\n.save") \
  -c -t 20 -fc 404
```
Used on: **Team** — discovered `script.old` containing FTP credentials.
