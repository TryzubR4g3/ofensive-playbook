# Windows service and task hardening

<!-- tags: Windows, services, task scheduler, scheduled task, service account, host privilege, Sysmon -->

Service and task configurations define what runs, who can manage it and which identity receives its privileges.

## Checks

- Review service and task identities against the roles required by their workloads.
- Compare configured executable paths, owners and ACLs with the host baseline.
- Correlate service creation, configuration changes and task registration with change records.

## Mitigation

Use explicit executable paths, dedicated identities and restricted write permissions for binaries, scripts and configuration. Monitor changes to high-privilege workload definitions.

## References

- [Directory identity review](directory-access-review.md)
- [Unix host privilege review](host-privilege-review.md)
- [Windows event log review](../tools/windows-event-logs.md)
