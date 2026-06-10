# Yum Sudo Plugin Injection

Privilege escalation through sudo-allowed `yum` plugin/script execution.

Used on: **Daily Bugle**

## Prerequisites

- `sudo -l` allows `yum` or a yum-related helper.
- Ability to control a plugin, config or package scriptlet loaded by yum.

## Steps

<!-- cmd: linux -->
```bash
sudo -l
sudo yum <controlled-action>
```

## Notes

- This note is intentionally short until the Daily Bugle writeup is finalized.
- Preserve exact plugin paths and payloads in the writeup and duplicate reusable pieces into `payloads/`.

