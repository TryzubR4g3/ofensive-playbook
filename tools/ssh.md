# ssh / ssh-keygen

Standard SSH client, used for login with reused credentials, private-key authentication and local port forwarding to pivot into internal services.

## Commands Used

### Login with reused password
```bash
ssh ben@TARGET_IP
```
Used on: **Silentium** — `SMTP_PASSWORD` from container env reused as host password.

```bash
ssh mark@TARGET_IP
ssh sa_mark@TARGET_IP
```
Used on: **CCTV**

### Login with private key obtained through symlink write
```bash
ssh -i /tmp/htb_key root@TARGET_IP
```
Used on: **Silentium**

### Local port forwarding (tunnel to bound-localhost service)
```bash
ssh -L 8080:127.0.0.1:3001 ben@TARGET_IP
```
Used on: **Silentium** — expose Gogs (`127.0.0.1:3001`) on local `8080`.

```bash
ssh -L 8765:127.0.0.1:7999 sa_mark@TARGET_IP
```
Used on: **CCTV** — expose motionEye (`127.0.0.1:7999`) on local `8765`.

### Login with private key recovered via LFI
```bash
ssh -i dale_id_rsa dale@team.thm
```
Used on: **Team** — Dale's private key read from the target via LFI on `sshd_config`.

### Login with reused database credentials
```bash
ssh drac@TARGET_IP
# Password: Th3dRaCULa1sR3aL  (found in .bash_history)
```
Used on: **IDE**

### Generate SSH key pair (no passphrase)
```bash
ssh-keygen -t rsa -f /tmp/htb_key -N ""
```
Used on: **Silentium** — key later written into `/root/.ssh/authorized_keys` via the symlink write.

### Generate SSH key pair for dual-session authentication agent
```bash
ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa_drac
```
Used on: **IDE** — required two stable key-auth sessions to run `pkttyagent` alongside `pkexec`.
