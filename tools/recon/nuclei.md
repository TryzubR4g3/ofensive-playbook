# nuclei

Template-based scanner for quick checks against known exposures, CVEs, and common web misconfigurations.

## Commands Used

### Scan a web target

<!-- cmd: linux -->
```bash
nuclei -target http://internal.thm/
```

Used on: **Internal**

identified WordPress, XML-RPC exposure, a user enumeration finding, and an SSH Terrapin finding.

<!-- cmd: linux -->
```bash
nuclei -target http://$TARGET
```

Used on: **Gaara**

quick web scan after directory brute forcing returned no useful application paths.

## Related

- [../../exploits/web-rce/wordpress-theme-editor-webshell.md](../../exploits/web-rce/wordpress-theme-editor-webshell.md)


