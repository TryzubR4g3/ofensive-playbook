# Lookup

**Status:** WIP / incomplete.
**Note:** Initial access and privesc are not yet documented.

## Recon
```bash
nmap -sS --min-rate 5000 -p- -Pn -n --open $TARGET -oN silent
nmap -sVC -p $TARGET -oN service
```

**Output**
```

PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 8.2p1 Ubuntu 4ubuntu0.9 (Ubuntu Linux; protocol 2.0)
80/tcp open  http    Apache httpd 2.4.41 ((Ubuntu))
|_http-title: Did not follow redirect to http://lookup.thm
|_http-server-header: Apache/2.4.41 (Ubuntu)
```
### Host Setup
```bash
# What it does: adds machine domains to /etc/hosts.
# Why here: resolve virtual hosts during web enumeration.
echo "$TARGET lookup.thm" | sudo tee -a /etc/hosts
```

### Subdomain fuzzing
```bash
gobuster vhost -u http://lookup.thm \  
  -w /usr/share/wordlists/seclists/Discovery/DNS/subdomains-top1million-5000.txt \
  --append-domain
```
**Output**
```
#www.lookup.thm Status: 400 [Size: 336]
#mail.lookup.thm Status: 400 [Size: 336]
#smtp.lookup.thm Status: 400 [Size: 336]
```


## Related Notes

- [nmap](../../../tools/recon/nmap.md)
- [gobuster](../../../tools/fuzz/gobuster.md)
