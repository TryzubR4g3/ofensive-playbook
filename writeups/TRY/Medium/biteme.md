# biteme

**Status:** WIP / incomplete.
**Note:** Only recon and initial fuzzing documented. Needs completion.

## Recon 

```bash
# What it does: scan the target for open ports using the silent-scan alias and perform service enumeration.
# Why here: discover open services before targeting the web application.
nmap -sS -p- -n -Pn --min-rate 5000 $TARGET -oN silent
nmap -sVC -p22,80 $TARGET -oN service
```

## Web Enumeration

```bash
# What it does: brute-force directories on the web server.
# Why here: discover hidden paths like /console.
feroxbuster -u http://$TARGET -w /usr/share/seclists/Discovery/Web-Content/DirBuster-2007_directory-list-2.3-medium.txt
```

Accessing the `/console` directory reveals a login panel protected by a captcha.
Investigating the page source code reveals an obfuscated JavaScript message.

```javascript
Exp('\b'+e(c)+'\b','g'),k[c]);return p}('0.1(\'2\').3=\'4\';5.6(\'@7 8 9 a b c d e f g h i... j\');',20,20,'document|getElementById|clicked|value|yes|console|log|fred|I|turned|on|php|file|syntax|highlighting|for|you|to|review|jason'.split('|'),0,{}))
  return true;
}
```

This decodes to: "fred I turned on php file syntax highlighting for you to review jason".

### Fuzzing `/console`

```bash
# What it does: fuzz for specific file extensions within the /console path.
# Why here: search for hidden files that might have source code highlighted (as hinted by the message).
ffuf -u http://$TARGET/console/FUZZ -w /usr/share/wordlists/dirb/common.txt -e .php,.bak,.txt,.old
```

**Output**
```text
config.php              [Status: 200, Size: 0, Words: 1, Lines: 1, Duration: 35ms]
css                     [Status: 301, Size: 320, Words: 20, Lines: 10, Duration: 24ms]
dashboard.php           [Status: 302, Size: 0, Words: 1, Lines: 1, Duration: 23ms]
functions.php           [Status: 200, Size: 0, Words: 1, Lines: 1, Duration: 23ms]
index.php               [Status: 200, Size: 3961, Words: 306, Lines: 40, Duration: 25ms]
robots.txt              [Status: 200, Size: 25, Words: 3, Lines: 2, Duration: 24ms]
```

## Related Notes

- [nmap](../../../tools/recon/nmap.md)
- [feroxbuster](../../../tools/fuzz/feroxbuster.md)
- [ffuf](../../../tools/fuzz/ffuf.md)