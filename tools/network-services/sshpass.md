# sshpass

Non-interactive ssh password provider. Extremely useful when scripting ssh connections or when you cannot provide a password interactively.

## Commands Used

### Basic usage
Provide the password inline and execute the ssh command:
<!-- cmd: linux -->
```bash
sshpass -p 'MySecretPassword' ssh user@$TARGET
```
Used on: **marketplace**

### Execute a specific command remotely
<!-- cmd: linux -->
```bash
sshpass -p 'MySecretPassword' ssh user@$TARGET "cat /home/user/user.txt"
```

## Defensive Note
Passwords supplied via the command line (like `-p`) will be saved in the `~/.bash_history` file and visible to other users via the `ps` command. Use carefully.
