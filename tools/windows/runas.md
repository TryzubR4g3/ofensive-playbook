# runas

Windows built-in utility to execute programs using different credentials. 

## Memory Injection / Network Authentication (`/netonly`)

Injects credentials into memory for network connections ONLY. The local process runs under your current user, but any remote authentication uses the injected credentials.
The password is not validated by the DC locally, so it accepts anything until you actually make a network connection.

<!-- cmd: windows -->
```cmd
runas.exe /netonly /user:$DOMAIN\$USER cmd.exe
# Prompts for password interactively
```
Used on: **adenumeration**

### Using the injected session
Once the new `cmd.exe` spawns, any network tool launched from it uses the injected ticket/hash:
<!-- cmd: windows -->
```cmd
# NTLM Authentication
dir \\$TARGET_IP\SYSVOL

# Kerberos Authentication (if FQDN is used)
dir \\$DOMAIN\SYSVOL
```

## Saved Credentials (`/savecred`)

If an administrator has previously used `/savecred` and the credentials are still cached in the Windows Vault (`cmdkey /list`), you can spawn a shell as them without knowing the password.

<!-- cmd: windows -->
```cmd
runas /savecred /user:administrator cmd.exe
```
Used on: **Relevant privesc notes**
