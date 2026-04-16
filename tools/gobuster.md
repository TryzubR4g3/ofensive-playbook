# gobuster

Brute-force tool for directories, DNS subdomains and virtual hosts. Used primarily for vhost discovery in the writeups.

## Commands Used

### Virtual host enumeration (HTTPS, insecure)
```bash
gobuster vhost -u https://kobold.htb \
  -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt \
  --append-domain -k
```
Used on: **Kobold**

- `vhost` — virtual host brute-force mode
- `--append-domain` — append the base domain to each word
- `-k` — skip TLS certificate validation

### Virtual host enumeration (HTTP)
```bash
gobuster vhost -u http://silentium.htb \
  -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt \
  --append-domain
```
Used on: **Silentium**

### Virtual host enumeration with vhost-style wordlist
```bash
gobuster vhost -u http://monitorsfour.htb \
  -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt \
  --append-domain
```
Used on: **MonitorsFour**
