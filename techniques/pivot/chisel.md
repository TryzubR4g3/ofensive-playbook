# Chisel Pivoting

Used on: **Wreath**

Chisel creates HTTP-based tunnels that work well when a compromised host can reach the attacker or another pivot, but the attacker cannot directly reach internal services.

## When to Use

- Direct inbound access to an internal host is blocked by a firewall.
- The compromised internal host can make outbound connections to the attacker or pivot.
- You have shell access to run custom binaries on the target.

## Why It Works

Chisel wraps TCP forwarding and SOCKS proxying inside client/server HTTP connections. Reverse mode is especially useful when inbound firewall rules block direct access to an internal host, but outbound traffic from that host to the pivot is allowed.

## Prerequisites

- Ability to run Chisel on at least one compromised host.
- One reachable Chisel server endpoint.
- Firewall rules allowing the chosen listener ports.

## Reverse SOCKS

See [tools/pivot/chisel.md](../../tools/pivot/chisel.md) for the exact commands.

Configure proxychains:

```ini
socks5 127.0.0.1 1080
```

Use TCP-connect scans through the proxy:

See [tools/pivot/chisel.md](../../tools/pivot/chisel.md) for the exact commands.

## Reverse Remote Port Forward

Expose an internal host through a pivot:

See [tools/pivot/chisel.md](../../tools/pivot/chisel.md) for the exact commands.

Traffic to `10.200.180.200:15001` is forwarded through the tunnel to `10.200.180.100:80`.

## Reverse Shell Relay

When a target can reach the pivot but not Kali:

See [tools/pivot/chisel.md](../../tools/pivot/chisel.md) for the exact commands.

The target connects to the pivot on `4444`, and Chisel carries the session back to Kali's local listener.

## Defensive Note

Monitor unexpected long-lived HTTP tunnels, restrict egress between internal segments, and alert on unauthorized binaries running from temporary directories.

## Related

- [../tools/chisel.md](../../tools/pivot/chisel.md)
- [../tools/proxychains.md](../../tools/pivot/proxychains.md)
- [ssh-tunneling.md](ssh-tunneling.md)
