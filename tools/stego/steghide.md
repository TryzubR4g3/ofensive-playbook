# steghide

Hides and extracts files inside JPEG, BMP, WAV and AU covers using LSB + DES encryption + passphrase. Ubiquitous in CTF image-loot tasks; on Kali: `sudo apt install steghide`.

Used on: **Yueiua**

## Commands Used

### Probe without a passphrase
```bash
steghide info oneforall.jpg
# Shows whether data is embedded, the embedded file name, and size —
# without requiring the passphrase. Great sanity check before guessing.
```

### Extract with a known passphrase
```bash
steghide extract -sf oneforall.jpg       # [USED — Yueiua]
# Enter passphrase:
# wrote extracted data to "creds.txt"
```
| Flag | Meaning |
|------|---------|
| `-sf <file>` | stego file (the image) |
| `-p <pass>` | passphrase on command line (skips prompt) |
| `-xf <out>` | explicit output filename |

### Extract non-interactively
```bash
steghide extract -sf oneforall.jpg -p 'AllmightForEver!!!' -xf creds.txt
```

### Embed (reverse — for planting payloads)
```bash
steghide embed -cf cover.jpg -ef secret.txt -p 'hunter2' -sf stego.jpg
```

## Passphrase Hunting

Steghide is passphrase-protected. In CTF chains the passphrase is almost always already on the box:

```bash
# On the foothold shell
grep -rEi 'pass|pwd|phrase|secret' /home /opt /tmp /var/www 2>/dev/null
cat /path/to/passphrase.txt
echo '<base64>' | base64 -d
```

## Brute-force with stegseek

`steghide` itself has no brute mode — use **stegseek** (drop-in, 40k+ guesses/sec):

```bash
sudo apt install stegseek   # or download from github.com/RickdeJager/stegseek
stegseek oneforall.jpg /usr/share/wordlists/rockyou.txt
# [i] Found passphrase: "hunter2"
# [i] Original file: "creds.txt"
```

## Failure Modes

| Output | Cause |
|--------|-------|
| `steghide: could not extract any data with that passphrase` | Wrong passphrase OR no data embedded |
| `the format of the file "X" is not supported` | JPEG/BMP/WAV only — PNG needs `zsteg` |
| `the file format of the file "X" is not supported (maybe it is corrupt)` | Magic bytes wrong — repair with `printf`+`dd` first |

If the file is PNG, pivot to `zsteg`. If it is any other format, pivot to `binwalk -e` or `foremost`.

## Related
- [exiftool](../web/exiftool.md) — always run first for cheap metadata wins
- [strings](../reversing/strings.md) — readable-strings fallback
- [hashcat](../creds/hashcat.md), [john](../creds/john.md) — alternate brute-force if stegseek finds nothing
- [steganography-image-loot.md](../../exploits/stego/steganography-image-loot.md) — full chain (magic fix ? exiftool ? steghide)


