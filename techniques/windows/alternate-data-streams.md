# Alternate Data Streams (ADS)

The NTFS file system supports Alternate Data Streams (ADS), which allows data to be hidden behind an existing file without altering the file's visible size or functionality. This is often used by attackers to hide malicious payloads.

Used on: **eJPT / Course Reference**

## 1. Creating and Writing to an ADS

You can hide a payload inside an ADS of an innocuous file (like a text file).

<!-- cmd: windows -->
```cmd
# Create an innocent file
echo "Normal file content" > normal.txt

# Hide text inside an ADS named 'hidden'
echo "Secret password" > normal.txt:hidden

# Hide a binary executable inside an ADS named 'payload.exe'
type C:\Temp\nc.exe > normal.txt:payload.exe
```

## 2. Viewing ADS Content

Standard `dir` commands won't show the ADS.

<!-- cmd: windows -->
```cmd
# List files along with their Alternate Data Streams
dir /r

# Read hidden text content using PowerShell or more/type tricks
more < normal.txt:hidden
powershell -c "Get-Content -Path normal.txt -Stream hidden"
```

## 3. Executing ADS Binaries

Executing a hidden binary stream varies by OS version, as modern Windows versions restrict direct execution of ADS.

<!-- cmd: windows -->
```cmd
# Older Windows (WMI approach)
wmic process call create "C:\full\path\to\normal.txt:payload.exe"

# Using a symlink or an external tool (like expand or esentutl) to extract it first
esentutl.exe /y "normal.txt:payload.exe" /d "C:\Temp\extracted.exe" /o
C:\Temp\extracted.exe
```
