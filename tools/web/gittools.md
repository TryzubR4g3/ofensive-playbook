# GitTools

Git repository recovery and history extraction toolkit. Useful after finding exposed `.git` folders or copying bare repositories from a compromised server.

## Commands Used

### Extract a copied bare repository

```bash
git clone https://github.com/internetwache/GitTools
/home/kali/Desktop/tools/GitTools/Extractor/extractor.sh . Website_extracted
```

Used on: **Wreath**

extracted `Website.git` from `C:\GitStack\repositories` to inspect historical source snapshots.

### Print commit metadata from extracted snapshots

```bash
separator="======================================="; for i in $(ls); do printf "\n\n$separator\n\033[4;1m$i\033[0m\n$(cat $i/commit-meta.txt)\n"; done; printf "\n\n$separator\n\n\n"
```

Used on: **Wreath**

reconstructed commit order before reviewing the latest PHP upload logic.

## Related

- [git](../devops/git.md)
- [php-exiftool-comment-webshell.md](../../exploits/web-rce/php-exiftool-comment-webshell.md)


