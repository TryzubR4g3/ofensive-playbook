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

- `-fc 404` - filter out 404 responses
- `-fw 2` - filter out responses with 2 words

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

- `-H` - inject custom `Host` header
- `-fs 0` - filter responses of size 0
- `-t 50` - 50 concurrent threads
- `-c` - colored output

### Fuzzing with file extensions
```bash
ffuf -u "http://cacti.monitorsfour.htb/cacti/FUZZ" \
  -H "Host: cacti.monitorsfour.htb" \
  -w /usr/share/wordlists/seclists/Discovery/Web-Content/DirBuster-2007_directory-list-2.3-big.txt \
  -e .php,.txt,.bak,.old,.sql,.env \
  -c -t 50 -fw 1,604
```
Used on: **MonitorsFour**

- `-e` - append extensions to each word
- `-fw 1,604` - filter responses with 1 or 604 words

### LFI parameter fuzzing (filter by word count)
```bash
ffuf -u "http://dev.team.thm/script.php?page=FUZZ" \
  -w /usr/share/wordlists/seclists/Fuzzing/LFI/LFI-Jhaddix.txt \
  -c -t 50 -fw 1,18
```
Used on: **Team**

- `-fw 1,18` - filter out baseline responses with 1 or 18 words

### Backup file extension brute-force
```bash
ffuf -u "http://team.thm/scripts/scriptFUZZ" \
  -w <(echo -e ".bak\n.old\n_backup\n.bkp\n~\n.txt\n.sh\n.orig\n.save") \
  -c -t 20 -fc 404
```
Used on: **Team** - discovered `script.old` containing FTP credentials.

### Hidden parameter discovery (the payload value forces a different response size)
```bash
ffuf -u "http://$TARGET:5000/api/v1/resources/books?FUZZ=/home/sid/.bash_history" \
  -w /usr/share/wordlists/seclists/Discovery/Web-Content/burp-parameter-names.txt \
  -fs 2 -mc all -fw 11
```
Used on: **Bookstore** - found the hidden `show=` parameter that turned into LFI -> Werkzeug PIN -> RCE. Full method: [hidden-parameter-fuzzing.md](../../exploits/web-disclosure/hidden-parameter-fuzzing.md).

- `-mc all` - keep every status code visible so 500-on-real-param doesn't get hidden by default 200-only matching.
- `-fs <baseline>` / `-fw <baseline>` - adjust after one run; `ffuf` prints the size/word histogram so you can pick the dominant baseline to filter.

### API version-pivot fuzz (find legacy `/v1/` when current `/v2/` is hardened)
```bash
ffuf -u "http://$TARGET:5000/api/FUZZ/resources/books" \
  -w /usr/share/wordlists/seclists/Discovery/Web-Content/raft-small-words.txt -fs 200
```
Used on: **Bookstore** - v1 was still wired up and accepted the hidden parameter v2 had blocked.

### Discover the parameter name on a single endpoint
```bash
ffuf -u "http://$TARGET/file.php?FUZZ" \
  -w /usr/share/wordlists/seclists/Discovery/Web-Content/big.txt -fw 3
```
Used on: **Recruit** - `cv` was the only parameter name that produced a different baseline (3 words = "Missing cv parameter").

### LFI parameter-value fuzz (file:// URI inside an SSRF-style fetcher)
```bash
ffuf -u "http://$TARGET/file.php?cv=file:///FUZZ" \
  -w /usr/share/wordlists/seclists/Fuzzing/LFI/LFI-Jhaddix.txt \
  -fw 2
```
Used on: **Recruit** - only paths inside the webroot returned content; everything else hit "Only local files are allowed" (2 words).

### Webroot `.php` source brute-force
```bash
ffuf -u "http://$TARGET/file.php?cv=file:///var/www/html/FUZZ.php" \
  -w /usr/share/wordlists/seclists/Discovery/Web-Content/raft-medium-words.txt -fw 2
```
Used on: **Recruit** - `config.php` leaked `$HR_PASSWORD = 'hrpassword123'`. Pair with [php-source-disclosure-lfi.md](../../exploits/web-disclosure/php-source-disclosure-lfi.md).

### POST login bruteforce (multi-wordlist)
```bash
ffuf -w usernames.txt:W1,/usr/share/wordlists/rockyou.txt:W2 -X POST -d "username=W1&password=W2" -H "Content-Type: application/x-www-form-urlencoded" -u http://$TARGET/customers/login -fc 200
```
Used on: **General** - template for brute-forcing a POST login form with two parameters.

### Extension fuzzing inside a discovered path
```bash
ffuf -u http://10.130.130.11/console/FUZZ -w /usr/share/wordlists/dirb/common.txt -e .php,.bak,.txt,.old
```
Used on: **biteme** - discovered `dashboard.php`, `config.php`, and `functions.php` inside a hidden console directory.

### WebDAV directory discovery
```bash
ffuf -u http://$TARGET/FUZZ \
  -w /usr/share/wordlists/seclists/Discovery/Web-Content/DirBuster-2007_directory-list-2.3-medium.txt
```
Used on: **bsidesgtdav** - found `/webdav`, later abused with default credentials and upload.

### Extension fuzzing inside a discovered dev path
```bash
ffuf -u http://$TARGET:8080/dev/FUZZ \
  -w /usr/share/wordlists/seclists/Discovery/Web-Content/common.txt \
  -e .php,.txt,.env
```
Used on: **coldvvars** - checked for PHP/text/env content below `/dev`.

### Directory fuzzing against a vhost
```bash
ffuf -u http://app.gridmark.io/FUZZ \
  -w /usr/share/seclists/Discovery/Web-Content/common.txt
```
Used on: **Parcel** - enumerated the Gridmark application after adding the vhost locally.
