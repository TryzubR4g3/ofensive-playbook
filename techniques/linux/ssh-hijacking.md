# SSH Hijacking

Used on: **Various**

SSH Hijacking allows an attacker with root or sufficient privileges to hijack an existing SSH session of another user, utilizing the active connection to issue commands or pivot.

## When to Use
- You have compromised a host as `root` and noticed other users are connected via SSH.
- You want to execute commands as another user without knowing their password or changing it.
- An administrator is currently logged in, and you want to piggyback on their session.

## Prerequisites
- `root` privileges on the target machine, or you are the same user running the `ssh` process.
- An active `sshd` session or `ssh-agent` running.

## How It Works
When a user connects via SSH, an SSH agent socket may be forwarded, or the TTY associated with their session can be controlled. By finding the `SSH_AUTH_SOCK` environment variable of the user's process, an attacker can use their forwarded agent to authenticate to other machines. Alternatively, `strace` or tools like `reptyr` can inject input into their TTY.

## Payload / Steps

### Stealing SSH Agent Socket
If the user forwarded their SSH agent (`ssh -A`), find their socket:

```bash
-- representative payload only
# Find the socket path for a specific user
grep -a SSH_AUTH_SOCK /proc/$(pidof sshd | awk '{print $1}')/environ
# Export the socket path
export SSH_AUTH_SOCK=/tmp/ssh-XXXXXX/agent.XXXX
# Use the hijacked agent to connect to another machine
ssh target-user@target-host
```

See [ssh.md](../../tools/network/ssh.md) for the full command reference.

## Variants
| Variant | When | Notes |
|---------|------|-------|
| SSH-Agent Hijacking | `ssh -A` was used | Allows lateral movement to other hosts using their keys |
| TTY Injection | You want to execute commands on their current host | Requires `ptrace` capabilities or `reptyr` |

## Defensive Note
Avoid using SSH Agent Forwarding (`-A`) unless absolutely necessary. Instead, use `ProxyJump` (`-J`) which does not expose the agent socket on the intermediate machine.

## Related
- [ssh.md](../../tools/network/ssh.md) — tool used to connect via SSH
