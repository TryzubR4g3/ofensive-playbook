# SUID Binary Reversing — Magic-Number Style

Used on: **Bookstore**

A custom-written SUID binary asks for a "secret" at runtime; if it matches, you get a root shell. Static reversing (no debugger, no library calls) cracks the comparison in five minutes when the binary is small.

The payoff: any `-rwsr-x---` binary owned by `root` and writable-only-by-root, that's not a known package binary, is a candidate. Shipping a custom SUID gatekeeper is a CTF cliché but also a real-world pattern (think internal tooling, "audit" wrappers).

## Prerequisites
- Foothold as a user that can execute the SUID (the group bit decides — Bookstore's `try-harder` was `-rwsr-sr-x sid`, so user `sid` could run it).
- `strings`, `ltrace`, `objdump` available — all in `binutils` and shipped on virtually every distro. If they aren't, scp the binary back to your box and analyse there.

## How It Works

The 3-stage funnel:

1. **`strings`** — printable strings = 4 chars. If the secret is ASCII-stored, you're done in seconds.
2. **`ltrace`** — every libc call with arguments. If the secret is compared with `strcmp` / `memcmp`, you read the arg directly. Useless if the comparison is inline.
3. **`objdump -d`** — raw assembly. Slow to read, but sees every constant and inline operation.

Most "magic number" SUID binaries fail at step 3, where you read the constants out of `xor` / `cmp` instructions and solve the equation in Python.

## Steps

### 1. Spot the SUID
```bash
find / -perm -4000 -type f 2>/dev/null
# /home/sid/try-harder
ls -la /home/sid/try-harder
# -rwsrwsr-x 1 root sid  8.3K Oct 20  2020 try-harder
file /home/sid/try-harder
# ELF 64-bit LSB executable, x86-64
```

A custom binary (no package, in a user's home, owned by root) screams "look at me".

### 2. Run it once — see what it asks for
```bash
./try-harder
# What's The Magic Number?!
1234
# Incorrect Try Harder
```

### 3. `strings` first
```bash
strings ./try-harder
strings ./try-harder | grep -iE "magic|number|secret|password|flag|/bin/"
```
If you see a literal answer, type it. Bookstore's binary stores `0x5dcd21f4` numerically -- nothing useful in `strings`. Move on.

### 4. `ltrace` — watch the comparison
```bash
ltrace ./try-harder
# __isoc99_scanf("%d", 0x7ffe...)  = 1
# puts("Incorrect Try Harder")     = 21
```
Only `scanf` and `puts`. **No** `strcmp` / `memcmp` -> the comparison is inline. Time for `objdump`.

### 5. `objdump -d` -- read the assembly
```bash
objdump -d ./try-harder | awk '/^.*<main>:/,/^$/'
```

Bookstore's `main` reduced to:
```asm
movl  $0x5db3, -0x10(%rbp)         ; mystery = 0x5db3
call  __isoc99_scanf@plt           ; scanf("%d", &input)
mov   -0x14(%rbp), %eax            ; eax = input
xor   $0x1116, %eax                ; eax ^= 0x1116
xor   %eax, -0xc(%rbp)             ; mystery ^= eax
cmpl  $0x5dcd21f4, -0xc(%rbp)      ; if (mystery == 0x5dcd21f4)
jne   <fail>                       ;     ... else fail
```

### 6. Solve it
```
((input ^ 0x1116) ^ 0x5db3) == 0x5dcd21f4
```
XOR is its own inverse, so:
```
input = 0x5dcd21f4 ^ 0x5db3 ^ 0x1116
```
```bash
python3 -c 'print(0x5dcd21f4 ^ 0x5db3 ^ 0x1116)'
# 1573454177
```

### 7. Cash in
```bash
./try-harder
# What's The Magic Number?!
1573454177
# id
# uid=0(root) gid=0(root) groups=0(root)
```

If the binary execs `/bin/bash -p` (preserving EUID), you keep root. If it execs `/bin/sh` you may need `-p` because bash drops privileges by default when EUID != UID -- look for the `execve` arg in `objdump`.

## Variants

| Pattern in `objdump` | What it means | Solution |
|----------------------|---------------|----------|
| `cmp $constant, %eax` after `scanf` | direct integer compare | answer = `constant` |
| `xor $A, %eax` ; `xor %eax, mystery` ; `cmp $B, ...` | layered XOR (Bookstore) | `input = B ^ mystery ^ A` |
| `call strcmp` (then `ltrace` shows the arg) | string compare | answer = the arg you saw |
| Loop with `xor` / `add` over each byte | rolling hash / custom check | re-implement the loop in Python and brute / invert |
| `setuid(0)` ; `system("/bin/bash")` | already root once you trigger the success branch | branch hijack with `gdb` / NX-off / patch the comparison |
| Calls `getenv("X")` first | env-var gate | set `X` before exec (`X=value ./binary`) |

## Defensive Note

- Don't ship custom SUID gates with secrets baked in. If you must, store the secret in a file root-only readable and `read()` it at runtime -- still bad, but the secret stops travelling with the binary.
- Replace home-grown auth checks with `polkit` / `sudo` rules.

## Related
- [strings](../../tools/reversing/strings.md) -- step 3
- [ltrace](../../tools/reversing/ltrace.md) -- step 4
- [objdump](../../tools/reversing/objdump.md) -- step 5
- [linux-enumeration.md](../enumeration/linux-enumeration.md) -- where the SUID hunt lives


