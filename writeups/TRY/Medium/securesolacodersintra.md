# SecureSolaCodersen Intranet — TryHackMe Writeup

<!-- brain:report -->
- **Platform** TryHackMe
- **Difficulty** Medium
- **Source status** Documented

## Report overview

The observations in this case inform a review of service and share exposure and evidence and artifact review.

## Defensive takeaways

- Confirm the intended audience for network services and shares, then compare their permissions and reachability with that policy.
- Record the source and timestamp of observed evidence and mark unverified conclusions separately.

## Defensive references

- [Exposed service and share hardening](../../../defense/techniques/service-exposure-review.md)
- [Evidence handling and artifact review](../../../defense/techniques/evidence-handling.md)

<!-- /brain:report -->

---


**Platform:** TryHackMe  
**Difficulty:** Medium  
**OS:** Linux  
**IP:** `$TARGET`  
**Tech Stack:** Apache (port 80), Werkzeug/Flask (port 8080), vsftpd 3.0.5, OpenSSH 8.2p1

---

## Attack Chain Overview

```
Port 8080 source comment leaks dev name (anders) and email domain
   → crunch-generated wordlist from developer identity
   → Credential attack → Flask login → foothold
   → Privilege escalation (TBD)
```

---

## Table of Contents

1. [Reconnaissance](#1-reconnaissance)
2. [Web Reconnaissance and Source Code Review](#2-web-reconnaissance-and-source-code-review)
3. [Custom Wordlist Generation with Crunch](#3-custom-wordlist-generation-with-crunch)
4. [Flask Application Attack](#4-flask-application-attack)
5. [Key Takeaways](#5-key-takeaways)

---

## 1. Reconnaissance

```bash
nmap -sS --min-rate 4000 -Pn -n -p- $TARGET -oN silent
nmap -sVC -p7,21,22,23,80,8080 $TARGET -oA service
```

**Output:**
```
PORT     STATE SERVICE    VERSION
7/tcp    open  echo
21/tcp   open  ftp        vsftpd 3.0.5
22/tcp   open  ssh        OpenSSH 8.2p1 Ubuntu 4ubuntu0.13
23/tcp   open  tcpwrapped
80/tcp   open  http       Apache httpd 2.4.41 ((Ubuntu))
8080/tcp open  http       Werkzeug httpd 2.2.2 (Python 3.8.10)
| http-title: Site doesn't have a title
|_Requested resource was /login
```

Notable services:
- Port 7: echo service (rare — may be useful for reflection/amplification tests)
- Port 23: `tcpwrapped` — possibly telnet, but filtered/wrapped
- Port 8080: Flask/Werkzeug login page — primary attack surface
- Port 21: FTP (vsftpd 3.0.5 — try anonymous login)

Related notes: [nmap](../../../tools/recon/nmap.md), [silent-scan](../../../tools/recon/silent-scan.md)

---

## 2. Web Reconnaissance and Source Code Review

Browsed to `http://$TARGET:8080` — redirected to `/login`. Examined the page source:

```html
<!-- Any bugs? Please report them to our developer team. We have an open bug bounty program!
  For any inquiries, contact devops@securesolacoders.no.
  Sincerely, anders (Senior Developer) -->
```

Key intelligence extracted:
- Developer username: **anders**
- Email domain: **securesolacoders.no**
- This is the only user identity visible at this stage — the password almost certainly follows a pattern derived from these values.

**Why comments matter:** HTML comments are invisible in the browser but trivially readable in the page source. Developers frequently leave internal contacts, debug notes, and credential hints in comments.

---

## 3. Custom Wordlist Generation with Crunch

The developer's name (`anders`) and the company domain (`securesolacoders.no`) are the only meaningful inputs we have. Generate permutation wordlists from these tokens using `crunch` in fixed-string permutation mode (`-p`):

```bash
# All permutations of "anders" and "SecureSolaCoders.no" (uppercase domain)
crunch 0 0 -p 'anders' 'SecureSolaCoders.no' > dict.txt

# All permutations of "anders" and "securesolacoders.no" (lowercase domain)
crunch 0 0 -p 'anders' 'securesolacoders.no' >> dict.txt
```

The `-p` flag in crunch generates all permutations of the supplied strings (concatenated without separators). The resulting wordlist covers `andersSolaSolaCoders.no`, `SecureSolaCoders.noanders`, etc.

> **Note:** In practice you would also add number suffixes, common separators (`_`, `-`, `.`), and case variants to cover more bases.

---

## 4. Flask Application Attack

Target: `http://$TARGET:8080/login` (Werkzeug/Flask app)

With username `anders` and the generated wordlist, brute-force the login form:

```bash
hydra -l anders -P dict.txt $TARGET -s 8080 http-post-form "/login:username=^USER^&password=^PASS^:Invalid"
```

> **Note:** Full exploitation output, foothold commands, and privilege escalation steps to be documented on completion.

Related notes: [hydra](../../../tools/creds/hydra.md)

---

## 5. Key Takeaways

1. **Developer identity in HTML comments is a direct credential lead.** Always view page source and check HTML comments — `anders` in a comment gave us the username for the attack without any further enumeration.
2. **Email domain + developer name = wordlist seed.** When you have a known username, build a wordlist from every token visible in the app (company name, domain, product name, first name, role). Crunch's `-p` permutation mode is the fastest way to cover all combinations.
3. **Multiple unusual ports deserve investigation.** Port 7 (echo), 23 (tcpwrapped), and a Werkzeug dev server all ran simultaneously. In CTF and lab environments, unusual port combinations are almost always deliberate.
4. **FTP and SSH should be tested with the same credentials** that unlock the web app — password reuse is endemic in these environments.

---

## Related Notes

- [nmap](../../../tools/recon/nmap.md)
- [hydra](../../../tools/creds/hydra.md)