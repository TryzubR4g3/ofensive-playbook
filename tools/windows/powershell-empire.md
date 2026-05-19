# powershell-empire

Post-exploitation C2 framework for listeners, stagers, agents, modules, and hop listeners.

## Commands Used

### Install and start Empire

```bash
sudo apt install powershell-empire starkiller
sudo powershell-empire server
```

Used on: **Wreath** - tested as a C2 option before falling back to Chisel for the later pivot.

### Connect the client

```bash
powershell-empire client
```

Used on: **Wreath**.

### Run Empire network scripts through Evil-WinRM

```bash
proxychains evil-winrm -u Administrator -H NTLM_HASH -i 10.200.180.150 -s /usr/share/powershell-empire/empire/server/data/module_source/situational_awareness/network
```

Used on: **Wreath** - loaded `Invoke-Portscan` helpers into the Evil-WinRM session.

```powershell
Get-Help Invoke-Portscan
Invoke-Portscan -Hosts 10.200.180.100 -TopPorts 50
```

Used on: **Wreath** - found ports `80` and `3389` on the final internal host.

## Related

- [powershell](powershell.md)
- [evil-winrm](evil-winrm.md)
- [powershell-empire-hop-listener.md](../../techniques/pivot/powershell-empire-hop.md)


