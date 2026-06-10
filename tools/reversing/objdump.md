# objdump

GNU binutils disassembler. Dumps the assembly of a binary's `.text` section so you can read the actual logic when `strings` / `ltrace` come up empty (inline comparisons, XOR obfuscation, magic numbers baked into instructions).

Always reach for this **after** `strings` and `ltrace` — `objdump` is the slowest to read but the only one that sees inline arithmetic.

## Commands Used

### Disassemble `main()` of a SUID binary
<!-- cmd: linux -->
```bash
objdump -d ./try-harder | awk '/^.*<main>:/,/^$/'
```
Used on: **Bookstore**

`-d` — disassemble executable sections.
- `awk '/<main>:/,/^$/'` — slice out only the `main` function (from the `<main>:` label to the next blank line). Saves you scrolling through libc stubs.

Output that solved Bookstore:
```asm
7cb:  movl  $0x5db3, -0x10(%rbp)     ; mystery = 0x5db3
7f9:  xor   $0x1116, %eax             ; eax = input XOR 0x1116
804:  xor   %eax, -0xc(%rbp)          ; result XOR mystery
807:  cmpl  $0x5dcd21f4, -0xc(%rbp)   ; compare with constant
```
That's enough to solve `(input ^ 0x1116) ^ 0x5db3 == 0x5dcd21f4` for the magic number — no debugger needed.

## Common Flags

| Flag | What it does |
|------|--------------|
| `-d` | Disassemble executable sections |
| `-D` | Disassemble **everything** (incl. `.data`, `.rodata`) |
| `-M intel` | Use Intel syntax instead of AT&T |
| `-S` | Mix source and disassembly when symbols/debug info are present |
| `-x` | Print all headers (sections, symbols, dynamic deps) |
| `-t` | Print symbol table |
| `-s -j .rodata` | Hex-dump a specific section (find embedded strings/keys) |
| `--disassemble=symbol` | Disassemble only one function (newer binutils) |

## Reading 64-bit AT&T syntax fast

| What you see | What it means |
|--------------|---------------|
| `mov $0x5db3, -0x10(%rbp)` | `local_var = 0x5db3` |
| `xor %eax, -0xc(%rbp)` | `local ^= eax` |
| `cmpl $X, %eax` | compare without storing — sets flags for next jump |
| `je <addr>` / `jne <addr>` | branch on equal / not equal |
| `call <symbol>` | function call (libc shows up as `<scanf@plt>`) |
| `leaq <str>(%rip), %rdi` | first arg = string at that address (`-s -j .rodata` to read it) |

## Related
- [strings](strings.md) — fast first pass
- [ltrace](ltrace.md) — runtime libcall tracing (fails on inline comparisons)
- [suid-binary-reversing.md](../../privesc/linux/suid-binary-reversing.md) — full reversing playbook


