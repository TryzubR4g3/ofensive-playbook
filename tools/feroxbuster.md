# feroxbuster

Fast, recursive web content discovery tool written in Rust. Used for directory and file brute-forcing against HTTP targets, including multi-port web applications.

## Commands Used

### Recursive directory brute-force (standard wordlist)
```bash
feroxbuster -u http://team.thm/ \
  -w /usr/share/seclists/Discovery/Web-Content/DirBuster-2007_directory-list-2.3-big.txt
```
Used on: **Team**

### Directory brute-force on non-standard port
```bash
feroxbuster -u http://TARGET_IP:62337/ \
  -w /usr/share/seclists/Discovery/Web-Content/big.txt
```
Used on: **IDE**

- Non-standard ports (e.g. `62337`) must be included explicitly in the URL
