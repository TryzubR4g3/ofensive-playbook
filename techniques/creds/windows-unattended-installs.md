# Searching For Passwords In Windows Configuration Files

During initial installation or large-scale automated deployments (like SCCM), system administrators often use Unattended Installation files. If these files are left behind and readable by standard users, they may contain plaintext or base64-encoded administrative passwords.

Used on: **eJPT / Course Reference**

## 1. Unattended Installation Files

Search the file system for common Unattend / Sysprep files:

<!-- cmd: windows -->
```cmd
dir /s /b c:\unattend.xml
dir /s /b c:\sysprep.inf
dir /s /b c:\sysprep.xml
dir /s /b c:\autounattend.xml
```

Common locations:
- `C:\Windows\Panther\Unattend.xml`
- `C:\Windows\Panther\autounattend.xml`
- `C:\Windows\System32\sysprep\sysprep.inf`
- `C:\Windows\System32\sysprep\sysprep.xml`

## 2. Extracting Credentials

Read the file and look for `<Password>` or `<AdministratorPassword>` tags.
<!-- cmd: cross-platform -->
```xml
<UserAccounts>
    <AdministratorPassword>
        <Value>UGFzc3dvcmQxMjMh</Value>
        <PlainText>false</PlainText>
    </AdministratorPassword>
</UserAccounts>
```

If `<PlainText>` is `false`, the value is usually Base64 encoded. Decode it on the attacker machine:
<!-- cmd: linux -->
```bash
echo "UGFzc3dvcmQxMjMh" | base64 -d
```

## 3. Other Configuration Files

Passwords might also be left in other files. Recursively search the `C:\` drive for the word "password":
<!-- cmd: windows -->
```cmd
# Using findstr (can be slow across the whole drive)
findstr /si password *.txt *.xml *.ini
```
