# John the Ripper

Offline password cracker. Used to crack extracted password hashes (bcrypt in this collection) against wordlists.

## Commands Used

### Crack a bcrypt hash with rockyou.txt
<!-- cmd: linux -->
```bash
echo '$2y$10$prZGnazejKcuTv5bKNexXOgLyQaok0hq07LW7AJ/QNqZolbXKfFG.' > mark.hash
john mark.hash --wordlist=/usr/share/wordlists/rockyou.txt
```
Used on: **CCTV**

produced `mark:opensesame`.

### Generic template
<!-- cmd: linux -->
```bash
john hash.txt --wordlist=/usr/share/wordlists/rockyou.txt
```
John auto-detects the format; `$2y$` identifies bcrypt.

### Crack a captured NTLMv2 hash (netntlmv2 format)
<!-- cmd: linux -->
```bash
echo '<NTLMv2 hash line from Responder>' > hash_ntlm.txt
john --format=netntlmv2 --wordlist=/usr/share/wordlists/rockyou.txt hash_ntlm.txt
```
Used on: **Ra**

Cracked `buse::WINDCORP:...` NTLMv2 hash captured via CVE-2020-12772 (Spark XMPP
`<img>` auto-fetch) → `buse:uzunLM+3131`. Must specify `--format=netntlmv2`
explicitly; John does not always auto-detect Net-NTLMv2.


