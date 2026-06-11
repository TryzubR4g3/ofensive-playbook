# Abusing SUID Binaries

Used on: **Various**

SUID (Set Owner User ID) is a special file permission in Linux that allows a user to execute a file with the permissions of the file's owner (usually `root`). Misconfigured SUID binaries are a primary vector for local privilege escalation.

## When to Use
- You have a low-privileged shell on a Linux system.
- You find unusual or custom binaries with the SUID bit set.
- Common binaries (like `find`, `vim`, `bash`, `cp`) have the SUID bit set by an administrator for convenience.

## Prerequisites
- A local shell on the target system.
- Execute permissions on the SUID binary.

## How It Works
When a binary is executed, it runs with the privileges of the user who invoked it. If the SUID bit is set, it runs with the privileges of the owner instead. If the binary allows escaping to a shell, reading files, writing files, or loading untrusted libraries, the attacker can leverage it to perform actions as the owner (e.g., `root`).

## Payload / Steps

Identify SUID binaries on the system:

```bash
-- representative payload only
find / -perm -4000 -type f -exec ls -la {} 2>/dev/null \;
```

See [suid-find-escape.md](../../privesc/linux/suid-find-escape.md) or [suid-binary-reversing.md](../../privesc/linux/suid-binary-reversing.md) for full exploit references.

## Variants
| Variant | When | Notes |
|---------|------|-------|
| Known Binaries (GTFOBins) | Binary is standard (e.g., `find`, `nmap`) | Refer to GTFOBins for the specific escape sequence. |
| Custom Binaries | Binary is non-standard | Requires reversing (e.g., `strings`, `ltrace`, `strace`) to find command injection or PATH hijacking vulnerabilities. |
| Shared Object Hijacking | Binary uses relative paths for `dlopen` | Create a malicious shared library in the path to be loaded and executed as root. |

## Defensive Note
Administrators should strictly limit the use of SUID bits and use `sudo` with specific command restrictions instead. Audit systems regularly for unexpected SUID binaries.

## Related
- [suid-find-escape.md](../../privesc/linux/suid-find-escape.md) — real instance of this technique
- [suid-binary-reversing.md](../../privesc/linux/suid-binary-reversing.md) — real instance of this technique
