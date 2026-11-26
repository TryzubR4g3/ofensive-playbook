# Unix host privilege review

<!-- tags: Linux, Unix, privilege boundaries, sudo, SUID, scheduled jobs, systemd, capabilities, least privilege -->

Review how a host grants elevated rights to applications, jobs, scripts and operators.

## Checks

- Compare authorized sudo rules and elevated file permissions with the build baseline.
- Review the owner, writable paths and execution identity of scheduled jobs and services.
- Limit required capabilities to the executable and service that need them.

## Mitigation

Use dedicated execution identities and least-privilege permissions. Keep executable code and its configuration writable only by their maintainers. Record baseline differences and add configuration checks to the image build.

## References

- [Windows service and task hardening](windows-service-hardening.md)
- [Exposed service hardening](service-exposure-review.md)
