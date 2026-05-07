# John the Ripper

Offline password cracker. Used to crack extracted password hashes (bcrypt in this collection) against wordlists.

## Commands Used

### Crack a bcrypt hash with rockyou.txt
```bash
echo '$2y$10$prZGnazejKcuTv5bKNexXOgLyQaok0hq07LW7AJ/QNqZolbXKfFG.' > mark.hash
john mark.hash --wordlist=/usr/share/wordlists/rockyou.txt
```
Used on: **CCTV** — produced `mark:opensesame`.

### Generic template
```bash
john hash.txt --wordlist=/usr/share/wordlists/rockyou.txt
```
John auto-detects the format; `$2y$` identifies bcrypt.
