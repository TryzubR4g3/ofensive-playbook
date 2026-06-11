# Holo

## Network Diagram

### Topology Overview

```
                        ┌─────────────────┐
                        │    DC-SRV01     │  🪟 Windows
                        │  10.200.65.30   │  Domain Controller
                        └────────┬────────┘
                                 │
              ┌──────────┬───────┴────────┬──────────┐
              │          │                │          │
       ┌──────┴──┐  ┌────┴────┐   ┌──────┴──┐  ┌───┴──────────┐
       │  S-SRV01 │  │ S-SRV02 │   │  L-SRV01 │  │ PC-FILESRV01 │
       │         │  │        │   │  🐧 Linux │  │             │
       └─────────┘  └────────┘   └────┬────┘  └─────────────┘
                                       │
                                ┌──────┴──────┐
                                │   L-SRV02   │  🐳 Docker
                                │192.168.100.100│
                                └─────────────┘
```

## Hosts Summary

| Hostname     | IP Address       | OS / Role              |
|--------------|------------------|------------------------|
| DC-SRV01     | 10.200.65.30     | Windows — Domain Controller |
| S-SRV01      | —                | Unknown OS             |
| S-SRV02      | —                | Unknown OS             |
| L-SRV01      | —                | Linux                  |
| PC-FILESRV01 | —                | File Server            |
| L-SRV02      | 192.168.100.100  | Linux — Docker         |

## Network Notes

- **DC-SRV01** (`10.200.65.30`) acts as the central node, likely a Windows Active Directory Domain Controller.
- **S-SRV01** and **S-SRV02** are directly connected to the DC with no visible IPs.
- **L-SRV01** is a Linux machine connected to the DC and serves as a pivot point to an internal subnet.
- **L-SRV02** (`192.168.100.100`) runs Docker and sits in a separate subnet (`192.168.100.0/24`), reachable through **L-SRV01**.
- **PC-FILESRV01** is a file server connected directly to the DC.

---

## Initial Reconnaice
```bash

```




