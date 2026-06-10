# Cadaver

Cadaver is a command-line WebDAV client, used to interact with WebDAV servers similar to a traditional FTP client (allowing upload, download, and manipulation of files).

Used on: **bsidesgtdav**

## Commands Used

Connect to a WebDAV server (prompts for credentials if required):

```bash
cadaver http://10.130.148.83/webdav/
```

Upload a file (from within the cadaver interactive shell):

```bash
dav:/webdav/> put reverse.php
```
