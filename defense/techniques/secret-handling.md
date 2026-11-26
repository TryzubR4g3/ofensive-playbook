# Credential exposure prevention

<!-- tags: secrets, credentials, private keys, credential reuse, configuration, backups, rotation -->

Review how applications store secrets and how operational artifacts can expose them to unintended readers.

## Checks

- Compare secret-store and configuration access with the identity inventory.
- Check whether backup, log or build outputs include credentials or private keys.
- Confirm that service credentials have an owner, scope and rotation procedure.

## Mitigation

Use scoped, short-lived credentials where supported. Restrict configuration and backup access and redact sensitive values in logs. Revoke or rotate exposed credentials and investigate their recorded use.

## References

- [Directory identity review](directory-access-review.md)
- [Evidence handling](evidence-handling.md)
