# Active Directory Enumeration — Notas

## 1. Obtener credenciales

Visitar el distribuidor de credenciales del lab:

```
https://distributor.za.tryhackme.com/creds
```

Credenciales obtenidas:

| Campo    | Valor            |
|----------|------------------|
| Username | connor.collins   |
| Password | Password1        |

---

## 2. Acceso inicial por SSH

```bash
ssh za.tryhackme.com\\connor.collins@thmjmp1.za.tryhackme.com
```

---

## 3. Inyección de credenciales con Runas

Desde la máquina Windows, inyectar las credenciales AD en memoria para autenticación de red:

```cmd
runas.exe /netonly /user:za.tryhackme.com\connor.collins cmd.exe
```

> La contraseña se introduce de forma **interactiva** al ejecutar el comando.

### Parámetros clave

| Parámetro  | Descripción |
|------------|-------------|
| `/netonly` | Las credenciales solo se usan para conexiones de red, no para sesión local |
| `/user`    | Dominio y usuario. Usar FQDN es más seguro que NetBIOS |
| `cmd.exe`  | Proceso a lanzar con las credenciales inyectadas |

> ⚠️ Con `/netonly` el DC **no valida** la contraseña al ejecutar el comando — acepta cualquier valor. Verificar manualmente en el siguiente paso.

---

## 4. Configurar DNS (Windows propio, no lab VM)

```powershell
$dnsip = "<DC IP>"
$index = Get-NetAdapter -Name 'Ethernet' | Select-Object -ExpandProperty 'ifIndex'
Set-DnsClientServerAddress -InterfaceIndex $index -ServerAddresses $dnsip
```

Verificar resolución:

```cmd
nslookup za.tryhackme.com
```

---

## 5. Verificar credenciales listando SYSVOL

Cualquier cuenta del dominio, por muy poco privilegiada que sea, puede leer SYSVOL:

```cmd
dir \\za.tryhackme.com\SYSVOL\
```

Si devuelve contenido → credenciales válidas y DNS funcionando ✅

> 💡 SYSVOL también puede contener **GPOs y scripts** con credenciales adicionales. Vale la pena enumerarlo.

---

## 6. IP vs Hostname — diferencia de autenticación

| Método              | Autenticación usada |
|---------------------|---------------------|
| `\\za.tryhackme.com\SYSVOL` | **Kerberos** (hostname en el ticket) |
| `\\<DC IP>\SYSVOL`          | **NTLM** (fuerza fallback) |

Usar IP fuerza NTLM → útil para evadir detección de ataques **OverPass-the-Hash / Pass-the-Hash** en red teams.

---

## 7. Enumeración con MMC + RSAT

### ¿Qué es?

Microsoft Management Console (MMC) con los Snap-Ins de **Remote Server Administration Tools (RSAT)** permite una vista gráfica completa del entorno AD. Se lanza desde el CMD abierto con `runas /netonly` para que use las credenciales inyectadas.

### Instalar RSAT (solo si usas tu propio Windows)

`Inicio → Apps & Features → Manage Optional Features → Add a feature → "RSAT: Active Directory Domain Services and Lightweight Directory Tools"`

### Configurar MMC

```
Inicio → Ejecutar → mmc
```

Una vez abierto:

1. `File → Add/Remove Snap-in`
2. Añadir los **3 Snap-ins de Active Directory**
3. Clic en los avisos/errores para ignorarlos
4. Clic derecho en **AD Domains and Trusts** → *Change Forest* → `za.tryhackme.com`
5. Clic derecho en **AD Sites and Services** → *Change Forest* → `za.tryhackme.com`
6. Clic derecho en **AD Users and Computers** → *Change Domain* → `za.tryhackme.com`
7. Clic derecho en **AD Users and Computers** (panel izquierdo) → `View → Advanced Features`

### Qué se puede enumerar

| Objeto         | Ruta en MMC                                      |
|----------------|--------------------------------------------------|
| Usuarios       | AD Users and Computers → za → People → [dept OU] |
| Servidores     | AD Users and Computers → za → Servers            |
| Workstations   | AD Users and Computers → za → Workstations       |
| Grupos         | Propiedades de cualquier usuario → Member Of     |
| Atributos      | Clic derecho sobre objeto → Properties           |

> 💡 Con permisos suficientes también se pueden **modificar objetos**: cambiar contraseñas, añadir usuarios a grupos, etc.

### Ventajas y limitaciones

| ✅ Ventajas | ❌ Limitaciones |
|------------|----------------|
| Vista holística del dominio | Requiere acceso GUI a la máquina |
| Búsqueda rápida de objetos | No permite recolección masiva de atributos |
| Modificación directa de objetos AD | — |

---

## 8. Enumeración con CMD — comando `net`

Útil cuando no hay GUI disponible, los defensores monitorizan PowerShell, o se ejecuta desde un RAT/payload.

> ⚠️ Requiere máquina **unida al dominio** (domain-joined). En máquina sin unir devuelve info del grupo WORKGROUP.

### Usuarios

```cmd
net user /domain
```
Lista todos los usuarios del dominio.

```cmd
net user <usuario> /domain
```
Detalle de un usuario: estado de cuenta, política de contraseña, grupos (hasta 10).

### Grupos

```cmd
net group /domain
```
Lista todos los grupos del dominio.

```cmd
net group "Tier 1 Admins" /domain
```
Lista los miembros de un grupo concreto.

### Política de contraseñas

```cmd
net accounts /domain
```

Devuelve información clave para planificar **password spraying**:

| Campo                        | Relevancia para ataque                        |
|------------------------------|-----------------------------------------------|
| Lockout threshold            | Máx. intentos antes de bloquear cuenta        |
| Lockout duration             | Tiempo de bloqueo si se supera el umbral      |
| Minimum password length      | Guía para construir wordlists                 |
| Maximum password age         | Indica si las contraseñas rotan               |
| Password history             | Cuántas contraseñas antiguas no se reutilizan |

### Ventajas y limitaciones

| ✅ Ventajas | ❌ Limitaciones |
|------------|----------------|
| Sin herramientas externas, a menudo no monitorizado | Solo funciona desde máquina domain-joined |
| No requiere GUI | Grupos truncados a 10 en detalle de usuario |
| Compatible con VBScript/macros de phishing | — |

---

## 9. Enumeración con PowerShell — cmdlets AD-RSAT

Acceso desde CMD con: `powershell`

> Los cmdlets se instalan automáticamente con RSAT (Task 3). Permiten apuntar a un dominio/servidor específico sin estar unido al dominio.

### Usuarios

```powershell
# Detalle completo de un usuario
Get-ADUser -Identity gordon.stevens -Server za.tryhackme.com -Properties *

# Filtrar usuarios por nombre
Get-ADUser -Filter 'Name -like "*stevens"' -Server za.tryhackme.com | Format-Table Name,SamAccountName -A
```

| Parámetro     | Descripción                                      |
|---------------|--------------------------------------------------|
| `-Identity`   | Nombre de cuenta a consultar                     |
| `-Properties` | Atributos a mostrar (`*` = todos)                |
| `-Server`     | DC a consultar (necesario sin domain-join)       |
| `-Filter`     | Filtro de búsqueda con operadores `-like`, `-gt` |

### Grupos

```powershell
# Info del grupo
Get-ADGroup -Identity Administrators -Server za.tryhackme.com

# Miembros del grupo
Get-ADGroupMember -Identity Administrators -Server za.tryhackme.com
```

### Objetos AD genéricos

```powershell
# Objetos modificados después de una fecha
$ChangeDate = New-Object DateTime(2022, 02, 28, 12, 00, 00)
Get-ADObject -Filter 'whenChanged -gt $ChangeDate' -includeDeletedObjects -Server za.tryhackme.com

# Cuentas con intentos fallidos de contraseña (útil antes de password spraying)
Get-ADObject -Filter 'badPwdCount -gt 0' -Server za.tryhackme.com
```

> 💡 Filtrar `badPwdCount -gt 0` antes de un spraying evita bloquear cuentas que ya tienen intentos fallidos acumulados.

### Dominio

```powershell
Get-ADDomain -Server za.tryhackme.com
```

Devuelve contenedores del dominio, DNS root, DC container, etc.

### Modificar objetos (explotación, no enumeración)

```powershell
# Forzar cambio de contraseña
Set-ADAccountPassword -Identity gordon.stevens -Server za.tryhackme.com `
  -OldPassword (ConvertTo-SecureString -AsPlaintext "old" -force) `
  -NewPassword (ConvertTo-SecureString -AsPlainText "new" -Force)
```

### Ventajas y limitaciones

| ✅ Ventajas | ❌ Limitaciones |
|------------|----------------|
| Mucha más info que `net` de CMD | PowerShell es más monitorizado por Blue Teams |
| Funciona desde máquina no domain-joined con `-Server` | Requiere instalar RSAT o scripts externos |
| Permite crear/modificar objetos AD | — |

---

## 10. Enumeración con BloodHound + SharpHound

### Concepto clave

> "Defenders think in lists, Attackers think in graphs."

BloodHound visualiza el entorno AD como un **grafo de nodos y aristas**, revelando rutas de ataque que las listas tradicionales no muestran. Usa **Neo4j** como base de datos backend.

**SharpHound** es el recolector de datos → **BloodHound** es la GUI de visualización.

### Tipos de collector (SharpHound)

| Collector            | Descripción |
|----------------------|-------------|
| `SharpHound.exe`     | Ejecutable Windows. El más común |
| `SharpHound.ps1`     | Script PS. Cargable en memoria (evade AV en disco). Ya no se actualiza |
| `AzureHound.ps1`     | Para entornos Azure / AAD |

> ⚠️ Las versiones de BloodHound y SharpHound **deben coincidir**. Este lab usa **v4.1.0**.

### Ejecutar SharpHound

```powershell
# Copiar al directorio de trabajo
copy C:\Tools\Sharphound.exe ~\Documents\
cd ~\Documents\

# Ejecución completa (primera vez)
.\SharpHound.exe --CollectionMethods All --Domain za.tryhackme.com --ExcludeDCs

# Ejecuciones posteriores (solo sesiones activas, más rápido)
.\SharpHound.exe --CollectionMethods Session --Domain za.tryhackme.com --ExcludeDCs
```

| Parámetro             | Descripción |
|-----------------------|-------------|
| `--CollectionMethods` | `All` = todo; `Session` = solo sesiones activas |
| `--Domain`            | Dominio a enumerar |
| `--ExcludeDCs`        | No tocar Domain Controllers → menos ruido/alertas |

Genera un **ZIP timestamped** con los datos en el directorio actual.

### Transferir el ZIP a Kali

```bash
scp <usuario>@THMJMP1.za.tryhackme.com:C:/Users/<usuario>/Documents/<archivo.zip> .
```

### Iniciar BloodHound (Kali/AttackBox)

```bash
neo4j console start      # Arrancar base de datos (puerto 7687)
bloodhound --no-sandbox  # En otra terminal
```

Credenciales por defecto Neo4j: `neo4j:neo4j`

Importar: arrastrar el ZIP al GUI de BloodHound.

### Qué se puede ver en BloodHound

**Node Info** (al hacer clic en un nodo de usuario):

| Sección                 | Qué muestra |
|-------------------------|-------------|
| Overview                | Sesiones activas, alcance a high-value targets |
| Node Properties         | Display name, título |
| Extra Properties        | Distinguished name, fecha de creación |
| Group Membership        | Grupos del usuario |
| Local Admin Rights      | Hosts donde tiene admin local |
| Execution Rights        | Capacidad de RDP, PSRemote, etc. |
| Outbound Control Rights | Objetos AD que este usuario puede modificar |
| Inbound Control Rights  | Objetos que pueden modificar a este usuario |

**Analysis Queries** (preconstruidas):
- *Find all Domain Admins*
- *Shortest Paths to Domain Admins*
- *Find Principals with DCSync Rights*, etc.

### Ejemplo de ruta de ataque

```
[Usuario AD] --RDP--> THMJMP1 <--Sesión activa-- [T1 Admin]
                          |
                    Escalada de privilegios
                          |
                       Mimikatz
                          |
                    NTLM hash T1 Admin
```

### Estrategia de recolección periódica

| Momento               | Método    | Motivo |
|-----------------------|-----------|--------|
| Inicio del assessment | `All`     | Estructura completa del dominio |
| ~10:00 h              | `Session` | Usuarios iniciando jornada |
| ~14:00 h              | `Session` | Usuarios volviendo de la comida |

> Limpiar sesiones antiguas: *Database Info → Clear Session Information* antes de cada import de sesiones.

### Ventajas y limitaciones

| ✅ Ventajas | ❌ Limitaciones |
|------------|----------------|
| Vista gráfica completa del dominio | SharpHound es ruidoso y detectable por AV/EDR |
| Muestra rutas de ataque automáticamente | — |
| Insights profundos sin queries manuales | — |

---

## 11. Técnicas adicionales de enumeración

Además de las cubiertas en este lab, otras técnicas relevantes:

| Técnica | Descripción | Referencia |
|---------|-------------|------------|
| **LDAP Enumeration** | Cualquier credencial válida puede hacer bind al DC vía LDAP y lanzar queries sobre objetos AD | [HackTricks LDAP](https://book.hacktricks.xyz/pentesting/pentesting-ldap) |
| **PowerView** | Script de reconocimiento del proyecto PowerSploit. Permite enumeración semi-manual de objetos AD | [GitHub PowerView](https://github.com/PowerShellMafia/PowerSploit/blob/master/Recon/PowerView.ps1) |
| **WMI (Windows Management Instrumentation)** | Usa el provider `root\directory\` para interactuar con AD desde PowerShell/CMD | [WMI AD Enum](https://0xinfection.github.io/posts/wmi-ad-enum/) |

---

## 12. Mitigaciones y detección

La enumeración AD es difícil de defender porque imita tráfico legítimo. Algunas contramedidas:

- **SharpHound** genera una cantidad anormal de eventos LogOn desde una sola cuenta → se pueden crear reglas de detección para este patrón.
- Crear reglas de **firma/detección** para binarios conocidos: SharpHound, RSAT tools, etc.
- **Monitorizar uso de CMD y PowerShell** desde cuentas no autorizadas.
- Los propios defensores pueden ejecutar estas técnicas periódicamente para **identificar y corregir misconfiguraciones** antes de que lo haga un atacante.

> El siguiente paso tras la enumeración es **escalada de privilegios y movimiento lateral** para alcanzar una posición desde la que ejecutar ataques.

---

## 13. Uso de credenciales inyectadas en aplicaciones

Con el CMD abierto via `runas /netonly`, **todas las conexiones de red** de ese proceso usarán las credenciales inyectadas:

- SQL Server Management Studio → autenticación Windows transparente
- Aplicaciones web con Windows Auth
- Herramientas de enumeración AD (BloodHound, etc.)