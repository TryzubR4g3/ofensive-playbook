# ssh / ssh-keygen

Standard SSH client, used for login with reused credentials, private-key authentication and local port forwarding to pivot into internal services.

## Commands Used

### Login with reused password
```bash
ssh ben@10.129.32.185
```
Used on: **Silentium** — `SMTP_PASSWORD` from container env reused as host password.

```bash
ssh mark@10.129.244.156
ssh sa_mark@10.129.244.156
```
Used on: **CCTV**

### Login with private key obtained through symlink write
```bash
ssh -i /tmp/htb_key root@10.129.32.185
```
Used on: **Silentium**

### Local port forwarding (tunnel to bound-localhost service)
```bash
ssh -L 8080:127.0.0.1:3001 ben@10.129.32.185
```
Used on: **Silentium** — expose Gogs (`127.0.0.1:3001`) on local `8080`.

```bash
ssh -L 8765:127.0.0.1:7999 sa_mark@10.129.244.156
```
Used on: **CCTV** — expose motionEye (`127.0.0.1:7999`) on local `8765`.

### Generate SSH key pair (no passphrase)
```bash
ssh-keygen -t rsa -f /tmp/htb_key -N ""
```
Used on: **Silentium** — key later written into `/root/.ssh/authorized_keys` via the symlink write.
