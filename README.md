# Second Brain â€” Offensive-Security Notebook

Personal, CLI-searchable knowledge base for offensive security work. The repo is **tool- and exploit-centric** â€” writeups are just the narrative shell. The real value is in `tools/` + `exploits/`, accessible from the terminal via the `brain` CLI.

- **`tools/`** â€” per-tool command notes (every flag I've actually used, tagged by machine).
- **`exploits/`** â€” per-technique playbooks (prerequisites, step-by-step, defensive notes).
- **`writeups/HTB/`, `writeups/TRY/`** â€” machine writeups that link to the reusable notes above.
- **`brain` CLI** â€” grep / list / recall without leaving the terminal.

---

## `brain` CLI

Topic-scoped search for tools, exploit playbooks and writeups. Tool notes do not keep writeup backlink lists; writeups link out to the reusable notes, and `brain backrefs` derives backlinks from those writeup links when you need them.

```bash
./brain guide                  # beginner examples: "what should I type?"
./brain <topic> [keyword]      # grep keyword inside a curated topic scope
./brain topics                 # list every topic with a one-line description

./brain find    <query>        # easy alias for broad search
./brain search  <query>        # case-insensitive grep across every .md
./brain cmd     <query>        # grep inside fenced code blocks only
./brain tool    [name]         # cat a tool note (or list all)
./brain exploit [name]         # cat an exploit note (or list all)
./brain writeup [name]         # cat a writeup (or list all)
./brain list    [tools|exploits|writeups|all]
./brain used-on <Machine>      # every note tagged "Used on: <Machine>"
./brain backrefs <note>        # every writeup that links to <note>
./brain open    <path>         # open in $EDITOR
```

Zero deps â€” pure Python 3. Works on Linux and Git Bash on Windows.

Spanish-friendly aliases exist for beginners: `guia`, `temas`, `buscar`, `comandos`, `herramienta`, `credenciales`, `privilegios`, `contenedor`, `base-datos`.

### Topics

| Topic | Covers |
|-------|--------|
| `recon` | Port scan, banner grab, directory brute |
| `enumeration` (`enum`) | Post-foothold system / AD / network enumeration |
| `fuzz` | Directory / vhost / parameter fuzzing |
| `exploit` | All exploit playbooks |
| `privesc` | Local privilege escalation (Linux + Windows) |
| `shells` | Reverse-shell one-liners and listener patterns |
| `creds` | Credential hunting, cracking, reuse |
| `pivot` | Port forwarding and tunnelling |
| `ad` | Active Directory / Kerberos / SMB / LDAP |
| `web` | Web / HTTP exploitation |
| `container` (`docker`) | Container / Docker abuse â€” incl. in-container enumeration |
| `stego` | Steganography / metadata loot |
| `reversing` (`re`, `binary`) | SUID / custom binary reverse engineering |
| `database` (`db`, `mongodb`, `sqlite`, `nosql`) | Backend DB enumeration & abuse (Mongo, SQLite, MySQL, Redis) |
| `sqli`, `lfi`, `rce` | Exactly what they say |

### Typical flow

```bash
./brain enumeration find              # every `find` command in enum tools/exploits
./brain fuzz ffuf                     # every ffuf invocation in fuzz-scoped files
./brain privesc sudo                  # privesc notes that mention sudo
./brain creds grep                    # credential-hunting greps
./brain ad kerberos                   # AD/Kerberos-specific commands
./brain web curl                      # curl usage in web exploits
./brain shells                        # all reverse-shell one-liners (scope list)
./brain used-on Overwatch             # every tool/exploit tagged with that machine
./brain exploit bash-eval             # exact match on an exploit note name
```

Output pattern (example - `brain enumeration find`):

```
exploits\linux-enumeration.md
  :77  find / -perm -4000 -type f 2>/dev/null      # [USED â€” DevArea]
  :92  ## Password & Credential Hunting with `find`
  used by:        # derived from writeup links, not stored in the tool note
    TRY\Easy\lazyadmin.md:179  Standard [Linux enumeration](exploits/enumeration/linux-enumeration.md)...
    HTB\Easy\cctv.md:210       [linux-enumeration.md](exploits/enumeration/linux-enumeration.md)
```

---

## HackTheBox Machines

### Easy

| Machine | OS | Writeup |
|---------|----|---------|
| **Silentium** | Linux | [Writeup ?](writeups/HTB/Easy/Silentium_HTB_Writeup.md) |
| **Kobold** | Linux | [Writeup ?](writeups/HTB/Easy/Kobold-Writeup.md) |
| **CCTV** | Linux | [Writeup ?](writeups/HTB/Easy/cctv.md) |
| **MonitorsFour** | Windows (Docker) | [Writeup ?](writeups/HTB/Easy/MonitorsFour.md) |

### Medium

| Machine | OS | Writeup |
|---------|----|---------|
| **DevArea** | Linux | [Writeup ?](writeups/HTB/Medium/DevArea.md) |
| **Overwatch** | Windows (AD) | [Writeup ?](writeups/HTB/Medium/Overwatch.md) |
| **Logging** ?? | Windows (AD) | [Writeup ?](writeups/HTB/Medium/Logging.md) |
| **VariaType** ?? | Linux (nginx) | [Writeup ?](writeups/HTB/Medium/VariaType.md) |

### Hard

*(None yet)*

---

## TryHackMe Machines

### Easy

| Machine | OS | Writeup |
|---------|----|---------|
| **Team** | Linux | [Writeup ?](writeups/TRY/Easy/Team.md) |
| **IDE** | Linux | [Writeup ?](writeups/TRY/Easy/Ide.md) |
| **Blueprint** | Windows (XAMPP) | [Writeup ?](writeups/TRY/Easy/blueprint.md) |
| **SoupedeCode 01** | Windows (AD) | [Writeup ?](writeups/TRY/Easy/soupedocde01.md) |
| **Anonforce (BSides GT)** | Linux | [Writeup ?](writeups/TRY/Easy/bsidesgtanonforce.md) |
| **VulnNet: Internal** | Linux | [Writeup ?](writeups/TRY/Easy/vulnnetinternal.md) |
| **Billing** | Linux (MagnusBilling) | [Writeup ?](writeups/TRY/Easy/billing.md) |
| **LazyAdmin** | Linux (SweetRice CMS) | [Writeup ?](writeups/TRY/Easy/lazyadmin.md) |
| **Yueiua** | Linux (PHP + stego) | [Writeup ?](writeups/TRY/Easy/yueiua.md) |
| **Vulnversity** | Linux (Apache + systemd privesc) | [Writeup ?](writeups/TRY/Easy/vulnversity.md) |
| **Vulnerability Capstone** | Linux (Fuel CMS) | [Writeup ?](writeups/TRY/Easy/vulnerabilitycapstone.md) |
| **Skynet** | Linux (Samba + SquirrelMail + Cuppa CMS) | [Writeup ?](writeups/TRY/Easy/Skynet.md) |
| **chronicle** | Linux (Werkzeug API + exposed Git repo) | [Writeup ?](writeups/TRY/Easy/chronicle.md) |
| **Lookup** ?? | Linux | [Writeup ?](writeups/TRY/Easy/Lookup.md) |
| **BSides GT Dav** | Linux (WebDAV) | [Writeup ?](writeups/TRY/Easy/bsidesgtdav.md) |
| **BSides GT Thompson** ?? | Linux (Tomcat) | [Writeup ?](writeups/TRY/Easy/bsidesgtthompson.md) |
| **checkmate** ?? | TBD | [Writeup ?](writeups/TRY/Easy/checkmate.md) |

### Medium

| Machine | OS | Writeup |
|---------|----|---------|
| **Bookstore** | Linux (Flask + Werkzeug debug) | [Writeup ?](writeups/TRY/Medium/bookstoreoc.md) |
| **Oh My Web** | Linux (Apache 2.4.49 in Docker) | [Writeup ?](writeups/TRY/Medium/ohmyweb.md) |
| **CMSpit** | Linux (Cockpit CMS + MongoDB) | [Writeup ?](writeups/TRY/Medium/cmspit.md) |
| **BSides GT â€” develpy** | Linux (Py2 daemon + Piet stego) | [Writeup ?](writeups/TRY/Medium/bsidesgtdevelpy.md) |
| **Recruit** | Linux (PHP LFI ? SQLi) | [Writeup ?](writeups/TRY/Medium/Recruit.md) |
| **Relevant** | Windows (IIS + SMB) | [Writeup ?](writeups/TRY/Medium/relevant.md) |
| **Operation Takeover** ?? | Linux (FRRouting) | [Writeup ?](writeups/TRY/Medium/operationtakeover.md) |
| **blog** | Linux (WordPress) | [Writeup ?](writeups/TRY/Medium/blog.md) |
| **coldvvars** ?? | Linux (SMB + web) | [Writeup ?](writeups/TRY/Medium/coldvvars.md) |

### Hard

| Machine | OS | Writeup |
|---------|----|---------|
| **Daily Bugle** ?? | Linux (Joomla) | [Writeup ?](writeups/TRY/Hard/dailybugle.md) |

### Networks

| Room | Difficulty | Writeup |
|------|------------|---------|
| **Wreath** | Easy | [Writeup ?](writeups/TRY/Networks/Easy/Wreath.md) |
| **Breaching Active Directory** | Medium | [Writeup ?](writeups/TRY/Networks/Medium/Breaching%20Active%20Directory.md) |
| **Bandit** ?? | Hard | [Writeup ?](writeups/TRY/Networks/Hard/Bandit.md) |
> ?? = writeup in progress / privilege escalation still being documented.

---

## Tools

Per-tool note with every command used across the writeups and a short description. Tool notes use `Used on: **Machine**` tags for search, but do not contain `Referenced in` / `Used by` backlink lists; the writeups own those references.

### Reconnaissance / Enumeration
- [nmap](tools/recon/nmap.md) â€” port & service discovery
- [whatweb](tools/recon/whatweb.md) â€” HTTP fingerprinting (server, CMS, redirects)
- [searchsploit](tools/recon/searchsploit.md) â€” offline Exploit-DB lookup
- [ffuf](tools/fuzz/ffuf.md) â€” web / API fuzzing
- [gobuster](tools/fuzz/gobuster.md) â€” vhost & directory brute-force
- [feroxbuster](tools/fuzz/feroxbuster.md) â€” recursive directory brute-force
- [wget](tools/web/wget.md) â€” bulk file download from webroot
- [netexec](tools/recon/netexec.md) â€” SMB / LDAP / MSSQL enumeration & spraying
- [smbclient](tools/recon/smbclient.md) â€” SMB share access
- [enum4linux](tools/recon/enum4linux.md) â€” SMB / RPC legacy sweep
- [showmount](tools/recon/showmount.md) â€” NFS export listing
- [ftp](tools/recon/ftp.md) â€” anonymous FTP triage + `mget`
- [impacket](tools/windows/impacket.md) â€” MSSQL client, AS-REP Roast, Kerberoast
- [kerbrute](tools/recon/kerbrute.md) â€” Kerberos-based password spraying
- [bloodhound](tools/recon/bloodhound.md) â€” AD ACL / session graph collection
- [ldap-utils](tools/recon/ldap-utils.md) â€” LDAP modify/search helpers for rogue LDAP setup

### Exploitation
- [curl](tools/web/curl.md) â€” HTTP payload delivery (JSON, SOAP, API abuse)
- [sqlmap](tools/web/sqlmap.md) â€” automated SQL injection
- [metasploit](tools/exploitation/metasploit.md) â€” public-exploit delivery
- [msfvenom](tools/exploitation/msfvenom.md) - payload artifact generation
- [responder](tools/creds/responder.md) â€” NTLM hash capture
- [dnstool](tools/recon/dnstool.md) â€” ADIDNS record manipulation
- [redis-cli](tools/database/redis-cli.md) â€” authenticated Redis enumeration
- [rsync](tools/network-services/rsync.md) â€” read/write file transfer via `rsync://` modules
- [mysql / mysqldump](tools/database/mysql.md) â€” DB enumeration + full-schema dump
- [sqlite3 / db_dump](tools/database/sqlite3.md) â€” SQLite + Berkeley DB file triage
- [mongo / mongosh](tools/database/mongo.md) â€” MongoDB shell, JS-REPL queries
- [exiftool](tools/web/exiftool.md) â€” image / PDF metadata
- [steghide](tools/stego/steghide.md) â€” extract hidden data from JPEG / BMP / WAV
- [getcap](tools/container/getcap.md) â€” POSIX file-capability enumeration

### Reverse Engineering
- [strings](tools/reversing/strings.md) â€” printable / UTF-16 string extraction
- [ltrace](tools/reversing/ltrace.md) â€” runtime library-call tracing
- [objdump](tools/reversing/objdump.md) â€” disassembly when `strings` / `ltrace` come up empty

### Shells & Pivoting
- [netcat](tools/pivot/netcat.md) â€” listeners & reverse shells
- [socat](tools/pivot/socat.md) â€” full-PTY reverse shells, port forwarding, TLS-wrap
- [ssh](tools/pivot/ssh.md) â€” login, key auth, local port forwarding
- [evil-winrm](tools/windows/evil-winrm.md) â€” interactive WinRM shell

### Post-Exploitation
- [docker](tools/container/docker.md) â€” container-based privilege escalation
- [git](tools/devops/git.md) â€” Gogs symlink push
- [tcpdump](tools/creds/tcpdump.md) â€” cleartext credential sniffing
- [powershell](tools/windows/powershell.md) â€” Windows enumeration & SOAP clients

### Password Cracking
- [john](tools/creds/john.md) â€” offline cracking (bcrypt, etc.)
- [hashcat](tools/creds/hashcat.md) â€” GPU cracking (NetNTLMv2, bcrypt)
- [gpg / gpg2john](tools/creds/gpg.md) â€” PGP passphrase + ciphertext decryption

---

## Exploits & Abuses

Per-technique note with the full chain (prereqs, commands, why it works).

### Web / Application RCE
- [MCP API injection](exploits/web-rce/mcp-api-injection.md) â€” Kobold `/api/mcp/connect`
- [Flowise Custom MCP Tool](exploits/web-rce/flowise-mcp-rce.md) â€” Silentium
- [Hoverfly middleware RCE](exploits/web-rce/hoverfly-middleware-rce.md) â€” DevArea
- [motionEye config injection](exploits/web-rce/motioneye-config-injection.md) â€” CCTV
- [WCF SOAP command injection](exploits/web-rce/wcf-soap-injection.md) â€” Overwatch
- [Cacti graph-template RCE](exploits/web-rce/cacti-rce.md) â€” MonitorsFour
- [Codiad 2.8.4 authenticated RCE (CVE-2018-14009)](exploits/web-rce/codiad-rce.md) â€” IDE
- [osCommerce 2.3.4 installer unauth RCE](exploits/web-rce/oscommerce-installer-rce.md) â€” Blueprint
- [MagnusBilling unauth RCE (CVE-2023-30258)](exploits/web-rce/magnusbilling-rce.md) â€” Billing
- [SweetRice CMS 1.5.1 Media Center RCE](exploits/web-rce/sweetrice-media-center-rce.md) â€” LazyAdmin
- [URL-parameter OS command injection](exploits/web-rce/url-param-command-injection.md) â€” Yueiua
- [Werkzeug debug console RCE (PIN via LFI)](exploits/web-rce/werkzeug-debug-rce.md) â€” Bookstore
- [Apache 2.4.49 path traversal ? RCE (CVE-2021-41773)](exploits/web-rce/apache-path-traversal-rce.md) â€” Oh My Web
- [Microsoft OMI unauthenticated RCE â€” OMIGOD (CVE-2021-38647)](exploits/web-rce/omigod-rce.md) â€” Oh My Web
- [Cockpit CMS unauth user enum + reset ? PHP upload (CVE-2020-35846)](exploits/web-rce/cockpit-cms-rce.md) â€” CMSpit
- [Python `input()` injection on a `socat`-hosted daemon](exploits/web-rce/python-input-injection.md) â€” BSides GT develpy
- [PHP file-upload extension bypass (`.phtml` / `.phar`)](exploits/web-rce/php-extension-bypass-upload.md) â€” Vulnversity
- [SMB write ? IIS execution (ASP webshell)](exploits/web-rce/smb-write-iis-execution.md) â€” Relevant
- [Fuel CMS 1.4 RCE](exploits/web-rce/fuel-cms-rce.md) â€” Vulnerability Capstone
- [Tomcat Manager WAR upload RCE](exploits/web-rce/tomcat-manager-war-upload.md) - BSides GT Thompson
- [WordPress crop-image RCE](exploits/web-rce/wordpress-crop-image-rce.md) - blog
- [SMB writable webroot to PHP execution](exploits/web-rce/smb-write-webroot-php-execution.md) - coldvvars
- [Rejetto HFS RCE](exploits/web-rce/rejetto-hfs-rce.md) - Steel Mountain
- [Joomla `com_fields` SQL injection](exploits/web-rce/joomla-com-fields-sqli.md) - Daily Bugle
- [Joomla template editor webshell](exploits/web-rce/joomla-template-editor-webshell.md) - Daily Bugle

### Web Read / SQLi / Disclosure
- [XPath login injection](exploits/web-auth/xpath-login-injection.md) - coldvvars
- [Git history disclosure](exploits/web-disclosure/git-history-disclosure.md) - chronicle
- [Apache CXF XOP Include ? LFI](exploits/web-disclosure/apache-cxf-xop-lfi.md) â€” DevArea
- [ZoneMinder time-based blind SQLi](exploits/web-disclosure/zoneminder-sqli.md) â€” CCTV
- [MailHog password reset](exploits/web-disclosure/mailhog-password-reset.md) â€” Silentium
- [Exposed `.env` / config files](exploits/web-disclosure/env-file-exposure.md) â€” MonitorsFour
- [Default credentials](exploits/web-disclosure/default-credentials.md) â€” CCTV, IDE
- [LFI via PHP `include()` parameter](exploits/web-disclosure/lfi-php-parameter.md) â€” Team
- [Backup / old script / SQL-dump exposure](exploits/web-disclosure/backup-file-exposure.md) â€” Team, LazyAdmin
- [Hidden parameter fuzzing (`ffuf` + payload-driven size diff)](exploits/web-disclosure/hidden-parameter-fuzzing.md) â€” Bookstore
- [`.DS_Store` information disclosure](exploits/web-disclosure/ds-store-disclosure.md) â€” Oh My Web
- [PHP source disclosure via restricted LFI (`file://` + `file_get_contents`)](exploits/web-disclosure/php-source-disclosure-lfi.md) â€” Recruit
- [SQL UNION injection â€” column extraction](exploits/web-disclosure/sql-union-injection.md) â€” Recruit
- [In-band SQL injection](exploits/sql-injection/in-Band-SQLi.md) â€” SQL Injection Fundamentals
- [Blind SQL injection authentication bypass](exploits/sql-injection/Blind-SQL-Injection.md) â€” SQL Injection Fundamentals
- [Boolean-based blind SQL injection](exploits/sql-injection/Blind-SQLi-Bollean-Based.md) â€” SQL Injection Fundamentals
- [Time-based blind SQL injection](exploits/sql-injection/Time-Based-Blind-SQL-Injection.md) â€” SQL Injection Fundamentals

- [Cuppa CMS `alertConfigField.php` LFI / RFI](exploits/web-disclosure/cuppa-cms-alertconfig-lfi-rfi.md) - Skynet

### Payloads
- [PHP exec Bash reverse shell](payloads/reverse-shells/php-exec-bash.md)
- [PHP proc_open reverse shell](payloads/reverse-shells/php-proc-open.md)
- [JSP WAR reverse shell](payloads/webshells/jsp-war-reverse-shell.md)
- [Python PTY stabilization](payloads/shell-stabilization/python-pty.md)
- [SSH authorized_keys persistence](payloads/persistence/ssh-authorized-keys.md)

### XSS
- [Stored XSS](exploits/xss/Stored-XSS.md)
- [Reflected XSS](exploits/xss/Reflected-XSS.md)
- [DOM-based XSS](exploits/xss/DOM-Based-XSS.md)
- [Blind XSS](exploits/xss/Blind-XSS.md)
- [XSS payloads](exploits/xss/XSS-Payloads.md)
### CI/CD & DevOps RCE
- [TeamCity super-user token ? build-step RCE](exploits/ci-cd/teamcity-superuser-token-rce.md) â€” VulnNet: Internal

### Network Service Abuse (Linux)
- [Anonymous FTP enumeration](exploits/network-services/anonymous-ftp-enumeration.md) â€” Anonforce
- [NFS share abuse (`showmount`, `no_root_squash`)](exploits/network-services/nfs-share-abuse.md) â€” VulnNet: Internal
- [Redis authenticated enumeration & abuse](exploits/network-services/redis-auth-abuse.md) â€” VulnNet: Internal
- [rsync module abuse (read + write)](exploits/network-services/rsync-module-abuse.md) â€” VulnNet: Internal
- [WebDAV upload to PHP RCE](exploits/network-services/webdav-upload-rce.md) - BSides GT Dav

### Active Directory / Windows
- [MSSQL linked server abuse](exploits/ad/mssql-linked-server.md) â€” Overwatch
- [MSSQL enumeration cheat sheet](exploits/ad/mssql-enumeration.md) â€” Overwatch
- [ADIDNS poisoning](exploits/ad/adidns-poisoning.md) â€” Overwatch
- [NTLM capture & crack](exploits/ad/ntlm-capture-crack.md) â€” Overwatch
- [Password spraying](exploits/ad/password-spraying.md) â€” Overwatch, SoupedeCode 01
- [AS-REP Roast & Kerberoast](exploits/ad/kerberos-roasting.md) â€” Overwatch, SoupedeCode 01
- [SMB anonymous enumeration](exploits/ad/smb-anonymous-enum.md) â€” Overwatch, SoupedeCode 01
- [RID brute-force enumeration (LSA cycling)](exploits/ad/rid-brute-enumeration.md) â€” SoupedeCode 01
- [Shadow Credentials ? PKINIT ? UnPAC-the-Hash](exploits/ad/shadow-credentials.md) â€” Logging
- [LDAP pass-back attack](exploits/ad/ldap-passback-attack.md) â€” Breaching Active Directory
- [NSSM-wrapped service abuse](exploits/privesc-windows/nssm-service-abuse.md) â€” Overwatch
- [PrintSpoofer SeImpersonate privesc](exploits/privesc-windows/printspoofer-seimpersonate.md) - Relevant

### Credential Hunting
- [Binary string credentials](exploits/creds/binary-credential-hunting.md) â€” Overwatch
- [systemd unit-file credentials](exploits/creds/systemd-service-credentials.md) â€” DevArea
- [`/proc/*/environ` enumeration](exploits/creds/env-variable-enum.md) â€” Silentium
- [Cleartext sniffing with tcpdump](exploits/creds/tcpdump-credential-sniffing.md) â€” CCTV
- [`.bash_history` credential discovery](exploits/creds/bash-history-credentials.md) â€” IDE
- [PGP private key cracking (`gpg2john`)](exploits/creds/pgp-key-cracking.md) â€” Anonforce
- [Steganography â€” hidden data in images](exploits/stego/steganography-image-loot.md) â€” Yueiua
- [Piet / `npiet` image steganography](exploits/stego/npiet-piet-stego.md) â€” BSides GT develpy
- [MongoDB enumeration from a foothold](exploits/creds/mongodb-enumeration.md) â€” CMSpit
- [Base64-encoded credentials in files / shares](exploits/creds/base64-encoded-credentials.md) â€” Relevant
- [Firefox credential extraction](exploits/creds/firefox-credential-extraction.md) - chronicle

### Privilege Escalation (Linux)
- [Docker group ? root](exploits/privesc-linux/docker-group-escape.md) â€” Kobold
- [Sudo + `bash` overwrite ? SUID root](exploits/privesc-linux/sudo-bash-overwrite.md) â€” DevArea
- [Gogs symlink write attack](exploits/privesc-linux/gogs-symlink-attack.md) â€” Silentium
- [Sudo script unsanitized input injection](exploits/privesc-linux/sudo-input-injection.md) â€” Team
- [Cron script group-writable abuse](exploits/privesc-linux/cron-script-abuse.md) â€” Team
- [pkexec + pkttyagent authentication agent](exploits/privesc-linux/pkexec-pkttyagent-privesc.md) â€” IDE
- [Sudo `fail2ban-client` ? SUID bash](exploits/privesc-linux/fail2ban-sudo-privesc.md) â€” Billing
- [Sudo-allowed script ? writable helper hijack](exploits/privesc-linux/sudo-script-helper-hijack.md) â€” LazyAdmin
- [Sudo bash `eval` filter bypass ? sudoers append](exploits/privesc-linux/bash-eval-filter-bypass.md) â€” Yueiua
- [Linux capabilities (`cap_setuid+ep`) ? root](exploits/privesc-linux/linux-capabilities-privesc.md) â€” Oh My Web
- [SUID binary reversing (XOR magic-number style)](exploits/privesc-linux/suid-binary-reversing.md) â€” Bookstore
- [`sudo exiftool -filename=` / CVE-2021-22204](exploits/privesc-linux/exiftool-sudo-cve-2021-22204.md) â€” CMSpit
- [Systemd unit drop / `systemctl` privesc](exploits/privesc-linux/systemd-service-privesc.md) â€” Vulnversity
- [Sudo `cat` arbitrary file read](exploits/privesc-linux/sudo-cat-file-read.md) - BSides GT Dav
- [SUID environment-variable gate bypass](exploits/privesc-linux/suid-env-var-checker.md) - blog
- [Tar wildcard injection](exploits/privesc-linux/tar-wildcard-injection.md) - Skynet
- [Yum sudo plugin injection](exploits/privesc-linux/yum-sudo-plugin-injection.md) - Daily Bugle

### Container Escape & Pivoting
- [Unauthenticated Docker API](exploits/container/docker-api-unauthenticated.md) â€” MonitorsFour
- [Container / Docker enumeration from inside](exploits/container/docker-container-enumeration.md) â€” Oh My Web, MonitorsFour, Silentium
- [Container network pivot via static binary](exploits/container/container-network-pivoting.md) â€” Oh My Web

### Pivoting
- [SSH port forwarding](exploits/pivot/ssh-tunneling.md) â€” Silentium, CCTV

### Enumeration Playbooks
- [Linux post-exploitation enumeration](exploits/enumeration/linux-enumeration.md) â€” system context, container detection, credential hunting with `find`/`grep`, SUID, cron, network
- [Windows post-exploitation enumeration](exploits/enumeration/windows-enumeration.md) â€” privileges, domain context, credentials on disk, services, scheduled tasks, payload transfer
- [SMB enumeration playbook](exploits/ad/smb-enumeration.md) â€” banner, signing, anonymous / guest / authenticated share walks, RID brute, spraying, Kerberos roasting, PTH

---

## Directory Structure

```text
.
+-- README.md
+-- CLAUDE.md          # project guide for Claude Code sessions
+-- brain              # bash wrapper for brain.py
+-- brain.py           # CLI search / list over tools, exploits, writeups
+-- writeups/
|   +-- HTB/
|   |   +-- Easy/
|   |   +-- Medium/
|   |   +-- Hard/
|   +-- TRY/
|       +-- Easy/
|       +-- Medium/
|       +-- Hard/
|       +-- Networks/
+-- tools/             # per-tool command notes
+-- exploits/          # real exploit / abuse notes
+-- payloads/          # reusable shells, webshells, snippets and persistence
```

---

## How to Use This Repo

Three-layer knowledge base, **with the layers inverted vs. a typical writeup repo**:

1. **Exploit notes** (`exploits/`) â€” the reusable techniques. Prereqs, step-by-step, variants, defensive notes. When I hit a similar box in 6 months, this is what I re-read.
2. **Tool notes** (`tools/`) â€” every flag I've actually used, tagged with the machine that needed it. `brain tool nmap` reminds me exactly how I used nmap on a specific AD box.
3. **Machine writeups** (`writeups/HTB/`, `writeups/TRY/`) â€” narrative shell. Short prose, ASCII chain diagram, then links down to the real artefacts. A writeup that duplicates commands instead of linking is a bug.

Every new machine that introduces a new tool / technique triggers an update to `tools/` or `exploits/` **in the same commit**, plus the `Used on: **<Machine>**` tag on the new note so `brain used-on <Machine>` picks it up. Add links from the writeup to the notes, not backlink sections inside the notes.

See `CLAUDE.md` for the full authoring rules and machine-closing checklist.

---

## Latest Additions

### TryHackMe Added from This Pass
- [Vulnerability Capstone](writeups/TRY/Easy/vulnerabilitycapstone.md) - Fuel CMS 1.4 RCE
- [Breaching Active Directory](writeups/TRY/Networks/Medium/Breaching%20Active%20Directory.md) - NTLM spray, LDAP pass-back, NetNTLM capture
- [Daily Bugle](writeups/TRY/Hard/dailybugle.md) - WIP, left in Spanish
- [Operation Takeover](writeups/TRY/Medium/operationtakeover.md) - WIP, left in Spanish
- [Bandit](writeups/TRY/Networks/Hard/Bandit.md) - WIP, left in Spanish
- [Skynet](writeups/TRY/Easy/Skynet.md) - SquirrelMail credential reuse, Cuppa CMS LFI/RFI, tar wildcard privesc
- [chronicle](writeups/TRY/Easy/chronicle.md) - exposed Git history, API key recovery, Firefox credential extraction

### Tools / Techniques Added from This Pass
- [ldap-utils](tools/recon/ldap-utils.md) - LDAP search/modify helpers
- [Fuel CMS 1.4 RCE](exploits/web-rce/fuel-cms-rce.md)
- [LDAP pass-back attack](exploits/ad/ldap-passback-attack.md)
- [SQL injection fundamentals](exploits/sql-injection/in-Band-SQLi.md)

### TryHackMe Networks
- [Wreath](writeups/TRY/Networks/Easy/Wreath.md) - Linux + Windows network chain

### Tools Added from Wreath
- [chisel](tools/pivot/chisel.md) - reverse SOCKS and remote port forwards
- [proxychains](tools/pivot/proxychains.md) - route CLI tools through SOCKS/HTTP pivots
- [FoxyProxy](tools/pivot/foxyproxy.md) - browser proxy profiles for web pivots
- [plink](tools/pivot/plink.md) - PuTTY command-line SSH tunnels from Windows
- [sshuttle](tools/pivot/sshuttle.md) - SSH-based transparent subnet routing
- [xfreerdp](tools/windows/xfreerdp.md) - RDP client with drive sharing
- [mimikatz](tools/windows/mimikatz.md) - Windows credential extraction
- [PowerShell Empire](tools/windows/powershell-empire.md) - C2 listeners, stagers and hop listeners
- [GitTools](tools/web/gittools.md) - extract and inspect recovered Git repositories

### Techniques Added from Wreath
- [Webmin 1.890 RCE](exploits/web-rce/webmin-cve-2019-15107-rce.md)
- [Chisel pivoting](exploits/pivot/chisel-pivoting.md)
- [GitStack 2.3.10 unauthenticated RCE](exploits/web-rce/gitstack-rce.md)
- [Windows admin access stabilization](exploits/privesc-windows/windows-admin-stabilization.md)
- [Mimikatz SAM dump and pass-the-hash](exploits/creds/mimikatz-sam-pth.md)
- [PowerShell Empire hop listener](exploits/pivot/powershell-empire-hop-listener.md)
- [PHP EXIF metadata webshell upload](exploits/web-rce/php-exiftool-comment-webshell.md)
- [Windows unquoted service path](exploits/privesc-windows/windows-unquoted-service-path.md)
- [Windows SAM hive dump](exploits/creds/windows-sam-hive-dump.md)

### TryHackMe Added
- [Kenobi](writeups/TRY/Easy/kenobi.md) - ProFTPd mod_copy, NFS key loot, SUID PATH hijack
- [Internal](writeups/TRY/Hard/Internal.md) - WordPress admin RCE, Jenkins Script Console, Docker secret hunting
- [Decryptify](writeups/TRY/Medium/Decryptify.md) - predictable PHP tokens and padding-oracle command injection

### Tools Added from Kenobi / Internal / Decryptify
- [smbmap](tools/recon/smbmap.md)
- [nuclei](tools/recon/nuclei.md)
- [wpscan](tools/web/wpscan.md)
- [hydra](tools/creds/hydra.md)
- [padre](tools/web/padre.md)

### Techniques Added from Kenobi / Internal / Decryptify
- [ProFTPd mod_copy SSH key loot](exploits/network-services/proftpd-mod-copy-rsa.md)
- [NFS mounted file loot](exploits/network-services/nfs-mounted-file-loot.md)
- [SUID PATH hijack](exploits/privesc-linux/suid-path-hijack.md)
- [WordPress theme editor webshell](exploits/web-rce/wordpress-theme-editor-webshell.md)
- [WordPress wp-config.php credential reuse](exploits/creds/wordpress-wp-config-credentials.md)
- [Jenkins HTTP form brute force](exploits/creds/jenkins-http-form-bruteforce.md)
- [Jenkins Script Console RCE](exploits/web-rce/jenkins-script-console-rce.md)
- [Docker container secret hunting](exploits/container/docker-container-secret-hunting.md)
- [Public log invite code disclosure](exploits/web-disclosure/public-log-invite-code-disclosure.md)
- [JavaScript obfuscated API key disclosure](exploits/web-disclosure/javascript-obfuscated-api-key.md)
- [PHP mt_rand token prediction](exploits/crypto/php-mt-rand-token-prediction.md)
- [Padding oracle to command injection](exploits/crypto/padding-oracle-command-injection.md)
