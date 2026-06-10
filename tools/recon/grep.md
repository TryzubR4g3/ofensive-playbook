# grep

`grep` is a command-line utility for searching plain-text data sets for lines that match a regular expression. In offensive workflows, it is heavily used to filter noisy output from other commands (like `find` or `ps`), extract specific tokens or capabilities, and recursively hunt for hardcoded credentials inside configuration files and logs.

---

## Commands Used

### Filtering Noise from Command Output
<!-- cmd: linux -->
```bash
find / -type f -name "*.txt" 2>/dev/null | grep -v proc
ps aux | grep sshd | grep -v grep
```
Used on: **Kobold**, **cctv**, **Internal**, **Ide**

- `-v` — inverts the match, filtering out lines containing the string (e.g., hiding noisy `/proc` filesystem results or the `grep` process itself in `ps` output).

### Hunting for Hardcoded Credentials
<!-- cmd: linux -->
```bash
grep -rEi "pass|key|secret|token" /mnt/nfs_conf/ 2>/dev/null
grep -r -E -i 'password|passwd|PASSWORD' /var/log/
```
Used on: **vulnnetinternal**, **silverplatter**, **yueiua**

- `-r` — recursive search through all files in the specified directory.
- `-E` — enables extended regular expressions, allowing the use of `|` for logical OR.
- `-i` — ignores case sensitivity.

### Extracting SUID/Capabilities
<!-- cmd: linux -->
```bash
cat /proc/self/status | grep -E '^Cap'
cat /proc/self/status | grep CapEff
```
Used on: **MonitorsFour**, **Internal**, **ohmyweb**

- `^` — regex anchor that matches the beginning of the line, useful for isolating capability masks in process statuses.

### Parsing Specific Values with Context
<!-- cmd: linux -->
```bash
cat /TeamCity/logs/catalina.out | grep -A1 -i "super user"
```
Used on: **vulnnetinternal**

- `-A1` — prints 1 line of trailing context after matching lines. Used here because the Super User token is often printed on the line immediately following the "Super user" log entry.

### Extracting and Formatting Matched Text
<!-- cmd: linux -->
```bash
grep -o '"Id":"[^"]*"' | cut -d'"' -f4
```
Used on: **MonitorsFour**

- `-o` — prints only the matched (non-empty) parts of a matching line, rather than the entire line. Crucial when parsing JSON or long strings to pipe into `cut` or `awk`.

## Related
- [linux-enumeration.md](../../exploits/enumeration/linux-enumeration.md)
- [find.md](find.md)
