# apktool

A tool for reverse engineering 3rd party, closed, binary Android apps. It can decode resources to nearly original form and rebuild them after making some modifications. Used to extract `strings.xml`, `AndroidManifest.xml`, and other resources from an APK.

## Commands Used

### Decode an APK

<!-- cmd: linux -->
```bash
apktool d nombre_del_apk.apk -o output_folder/
```
Used on: **Borderlands**, **dead-drop**

Decompiled the `mobile-app-prototype.apk` and `deaddrop-mobile.apk` to extract hardcoded credentials and API keys stored in `res/values/strings.xml`.

## Notes
- `d` - Decode mode.
- `-o` - Specify output directory.
- After decoding, `grep -r` is usually the next step to find sensitive information like `password`, `api_key`, or `token`.
