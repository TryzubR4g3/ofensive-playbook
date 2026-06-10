# jadx

Dex to Java decompiler. Provides a GUI and CLI to decompile Android Dex and Apk files to Java source code. Useful for reading the logic of an application and identifying how hardcoded secrets are used.

## Commands Used

### Open DEX or APK in GUI

<!-- cmd: linux -->
```bash
jadx-gui classes.dex
```
Used on: **Borderlands**

Used to reverse engineer the custom encryption routine for the API key in the `mobile-app-prototype.apk`. The decompiled Java code showed how the key was decrypted and used in API requests.

## Notes
- Often used alongside `apktool` (which extracts resources like `strings.xml`), whereas `jadx` provides readable Java code from the Dalvik bytecode.
