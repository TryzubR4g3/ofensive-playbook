# borg

BorgBackup (short for Borg) is a deduplicating backup program. Optionally, it supports compression and authenticated encryption. Used to extract backup repositories found during enumeration.

## Commands Used

### List a Borg repository
```bash
borg list .
```
Used on: **cyborgt8** - listed the contents of a downloaded Borg repository. Prompted for a passphrase which was cracked previously.

### List contents of a specific archive within a repository
```bash
borg list .::music_archive
```
Used on: **cyborgt8** - verified the contents of the `music_archive` before extraction.

### Extract a specific archive from a repository
```bash
borg extract .::music_archive
```
Used on: **cyborgt8** - extracted the contents of the `music_archive` to the local directory, yielding the user's `/home` directory and a notes file containing a plaintext password.

## Related

- [hashcat.md](../creds/hashcat.md)
