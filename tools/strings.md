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

Result: found a hardcoded MSSQL connection string →
`Server=localhost;Database=SecurityLogs;User Id=sqlsvc;Password=TI0LKcfHzZw1Vv;`
