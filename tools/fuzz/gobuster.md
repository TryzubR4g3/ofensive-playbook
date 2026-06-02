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

### Virtual host enumeration (HTTP, short wordlist)
```bash
gobuster vhost -u http://team.thm \
  -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt \
  --append-domain
```
Used on: **Team**



### Virtual host enumeration for a newly added host
```bash
gobuster vhost -u http://lookup.thm \
  -w /usr/share/wordlists/seclists/Discovery/DNS/subdomains-top1million-5000.txt \
  --append-domain
```
Used on: **Lookup**

### Directory brute-force with extension sweep
```bash
gobuster dir -u http://$TARGET \
  -w /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt \
  -x php,txt,html,bak,old,git \
  -o gobuster.txt
```
Used on: **Gaara** - checked for common web paths and backup/source extensions before moving to SSH brute force.

### Vhost enumeration against base domain
```bash
gobuster vhost -u http://gridmark.io \
  -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt \
  --append-domain
```
Used on: **Parcel** - checked for additional Gridmark virtual hosts after discovering `app.gridmark.io`.
