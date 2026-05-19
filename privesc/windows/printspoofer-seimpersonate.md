# PrintSpoofer SeImpersonate Privilege Escalation

Windows privilege escalation using `SeImpersonatePrivilege` with PrintSpoofer-style named-pipe abuse.

Used on: **Relevant**

## Prerequisites

- Shell as a service account with `SeImpersonatePrivilege`.
- Writable path to upload the binary.
- Listener or command payload for elevated execution.

## Steps

```cmd
whoami /priv
PrintSpoofer.exe -i -c cmd
```

## Notes

- Confirm the privilege first; without `SeImpersonatePrivilege`, this path is usually dead.
- Keep exact binary transfer and listener commands in the writeup.

