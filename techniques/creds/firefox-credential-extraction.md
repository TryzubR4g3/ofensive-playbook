# Firefox Credential Extraction

Recover saved Firefox credentials from a user's profile after obtaining local file access.

Used on: **chronicle**

## When to Use

- Local file access is obtained to a user's home directory
- A Firefox profile directory is discovered
- Files named `logins.json` and `key4.db` (or `key3.db`) are found on the filesystem

## Prerequisites

- Access to a Firefox profile directory.
- `logins.json` and the related key database (`key4.db` or legacy `key3.db`).

## Files To Hunt

```bash
find /home -name logins.json -o -name key4.db -o -name key3.db 2>/dev/null
```

## Notes

- Copy the profile files together; `logins.json` alone is not enough.
- Extracted credentials should feed password reuse checks against SSH, web panels or local services.

