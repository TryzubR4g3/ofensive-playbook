# nikto

Web server scanner for common misconfigurations, risky files, and known web server issues. Used as a quick web recon pass when directory brute forcing did not immediately produce useful results.

## Commands Used

### Scan a web target

```bash
nikto -h http://$TARGET
```

Used on: **Gaara** - run alongside Nuclei after initial web discovery returned little.
