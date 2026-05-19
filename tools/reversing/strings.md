# strings

GNU binutils utility that prints printable character sequences from binary files. Used to extract hardcoded credentials, connection strings and config fragments from compiled executables.

## Commands Used

### Extract Unicode (UTF-16LE) strings from a Windows binary and grep for credentials
```bash
strings -e l overwatch.exe | grep -iE "password|user|sql|connection"
```
Used on: **Overwatch**

- `-e l` — 16-bit little-endian strings (typical for .NET/Windows binaries)
- Piping through `grep -iE` narrows down the output to credential-looking lines.

Result: found a hardcoded MSSQL connection string ->
`Server=localhost;Database=SecurityLogs;User Id=sqlsvc;Password=TI0LKcfHzZw1Vv;`

### First-pass triage of an unknown SUID binary
```bash
strings ./try-harder | head -80
strings ./try-harder | grep -iE "magic|password|flag|key|/bin/"
```
Used on: **Bookstore**

Result: nothing useful — Bookstore's `try-harder` keeps the magic number in hex (`0x5dcd21f4`) inside an instruction, not as ASCII. That's the cue to escalate to [`ltrace`](ltrace.md) (libcalls) and then [`objdump`](objdump.md) (raw assembly).

- `strings` only catches **printable** runs = 4 chars. Numeric constants and `xor` keys never show.
- Always run it first — when it works, it's a 5-second win; when it doesn't, you've ruled out the easy case.

## Related
- [ltrace](ltrace.md) — runtime libcall tracing
- [objdump](objdump.md) — disassembly when `strings` and `ltrace` fail
- [suid-binary-reversing.md](../../privesc/linux/suid-binary-reversing.md) — full SUID-reversing chain


