# Web Discovery Playbook

A structured methodology for web enumeration and vulnerability discovery. 

## 1. Initial Reconnaissance & Fingerprinting

Before fuzzing, understand what you are attacking.

```bash
# Whatweb for tech stack fingerprinting
whatweb http://$TARGET

# Identify CMS, frameworks, and web servers
wappalyzer-cli http://$TARGET

# Map the raw headers and server responses
curl -I http://$TARGET
curl -i http://$TARGET
```

## 2. Directory and File Fuzzing

Find hidden paths, admin panels, and forgotten backups.

```bash
# Fast initial pass (common directories)
feroxbuster -u http://$TARGET -w /usr/share/seclists/Discovery/Web-Content/directory-list-2.3-medium.txt --status-codes 200,301,302,403

# Search for specific extensions based on the tech stack (e.g., php, txt, zip, bak)
gobuster dir -u http://$TARGET -w /usr/share/seclists/Discovery/Web-Content/directory-list-2.3-medium.txt -x php,txt,bak,zip,sql -t 50

# Fuzzing recursively (if a deep folder structure is found)
feroxbuster -u http://$TARGET/path/ -w /usr/share/seclists/Discovery/Web-Content/raft-large-directories.txt --depth 2
```

## 3. Virtual Host Enumeration

If the application redirects to a domain or uses Virtual Hosting, fuzz for subdomains.

```bash
# Gobuster Vhost mode (useful when DNS isn't resolving externally)
gobuster vhost -u http://$DOMAIN -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt --append-domain

# Ffuf Vhost fuzzing (filtering out default sizes)
ffuf -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt -H "Host: FUZZ.$DOMAIN" -u http://$TARGET -fs <size_of_default_page>
```

> 💡 **Tip:** Always add discovered vhosts to `/etc/hosts` immediately.

## 4. Parameter Fuzzing

If you find a page that might accept parameters (e.g. `index.php`, `view.php`), fuzz for hidden GET/POST parameters.

```bash
# Fuzz GET parameters
ffuf -w /usr/share/seclists/Discovery/Web-Content/burp-parameter-names.txt -u "http://$TARGET/page.php?FUZZ=test" -fs <size_of_default_page>

# Fuzz POST parameters
ffuf -w /usr/share/seclists/Discovery/Web-Content/burp-parameter-names.txt -u http://$TARGET/page.php -d "FUZZ=test" -X POST -H "Content-Type: application/x-www-form-urlencoded" -fs <size_of_default_page>
```

## 5. Technology-Specific Checks

| Technology | Playbook / Action |
|------------|-------------------|
| **WordPress** | `wpscan --url http://$TARGET -e u,vp,vt --api-token $TOKEN` |
| **Apache Tomcat** | Try default credentials (`tomcat:tomcat`, `tomcat:s3cret`, `admin:admin`) at `/manager/html` |
| **Jenkins** | Look for Script Console (`/script`) to execute Groovy payloads. |
| **PHP** | Look for LFI `?page=../../../etc/passwd` or command injection. |
| **API/JSON** | Fuzz for IDORs, map out the API endpoints using Postman or Burp. |

## 6. Known Exploits (CVEs)

Once you have identified exact versions (e.g. SweetRice CMS 1.5.1, Nostromo 1.9.6):

```bash
searchsploit "Software Name Version"
```
