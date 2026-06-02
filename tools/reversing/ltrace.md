# ltrace

Library-call tracer. Intercepts dynamic-library calls a process makes (`scanf`, `strcmp`, `getenv`, `printf`, etc.) and prints them with their arguments. Most useful for SUID binaries when you need to see comparisons / inputs without reaching for a debugger.

Use when:
- A binary asks for a "magic number / password" and you want to watch the comparison live.
- You want to know which file / env var the binary is reading.
- The binary is stripped — `ltrace` still resolves library calls because they go through the dynamic linker.

`ltrace` only sees **library** calls. If the comparison is implemented inline (e.g. `xor` + `cmp` in user code), nothing shows up — fall back to `objdump`.

## Commands Used

### Trace every libc call made by a SUID binary
```bash
ltrace ./try-harder
```
Used on: **Bookstore**

Result on Bookstore: `ltrace` printed `__isoc99_scanf("%d", ...)` but **no `strcmp` / `memcmp`** — the comparison was inline assembly (`xor` + `cmpl`), invisible to `ltrace`. Pivoted to `objdump` next.

- Run as the user that owns the SUID bit (or the binary may abort early when EUID  UID is unsafe).
- Combine with `-f` to follow forks, `-e <pattern>` to filter (e.g. `ltrace -e 'scanf*+strcmp'`).

## Common Flags

| Flag | What it does |
|------|--------------|
| `-f` | Follow `fork()` / `clone()` children |
| `-e func` | Trace only matching libcalls (`-e 'open*+read*'`) |
| `-o file` | Write trace to file (handy when output is huge) |
| `-S` | Also show raw syscalls (combines with strace-style output) |
| `-s 256` | Print up to 256 chars of string args (default 32 truncates passwords) |
| `-p PID` | Attach to a running process |

## Related
- [strings](strings.md) — first-pass string extraction
- [suid-binary-reversing.md](../../privesc/linux/suid-binary-reversing.md) — full reversing playbook


