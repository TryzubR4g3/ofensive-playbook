# Lookup

<!-- brain:report -->
- **Platform** TryHackMe
- **Difficulty** Easy
- **Source status** Documented

## Report overview

The observations in this case inform a review of Unix host privilege boundaries and authorization and account recovery.

## Defensive takeaways

- Review the execution identity and writable paths of elevated host services, jobs and binaries.
- Compare server-side authorization and account recovery with the documented access policy.

## Defensive references

- [Unix host privilege review](../../../defense/techniques/host-privilege-review.md)
- [Web authorization and account recovery](../../../defense/techniques/web-access-control.md)

<!-- /brain:report -->

---


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
  -w /usr/share/wordlists/seclists/Discovery/DNS/subdomains-top1million-20000.txt \
  --append-domain
```


## Related Notes

- [nmap](../../../tools/recon/nmap.md)
- [gobuster](../../../tools/fuzz/gobuster.md)
