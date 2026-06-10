# mcafee-sitelist-pwd-decrypt

A Python script used to decrypt McAfee SiteList passwords (`SiteList.xml` and `ma.db` `AUTH_PASSWD` fields) because McAfee uses a fixed, hardcoded encryption key across all deployments.
Repository: [funoverip/mcafee-sitelist-pwd-decryption](https://github.com/funoverip/mcafee-sitelist-pwd-decryption)

## Commands Used

### Decrypt an AUTH_PASSWD string
<!-- cmd: linux -->
```bash
python2 mcafee_sitelist_pwd_decrypt.py jWbTyS7BL1Hj7PkO5Di/QhhYmcGj5cOoZ2OkDTrFXsR/abAFPM9B3Q==
```
Used on: **Breaching-Active-Directory**

Decrypted the `AUTH_PASSWD` value extracted from `C:\ProgramData\McAfee\Agent\DB\ma.db` for the `svcAV` account, returning the plaintext password.

## Notes
- Typically requires Python 2 due to legacy crypto library usage.
- The input string is base64-encoded and contains the ciphertext encrypted with the known McAfee key.
