# Directory identity and delegated access review

<!-- tags: Active Directory, Kerberos, LDAP, NTLM, delegation, group membership, identity, least privilege -->

Directory controls depend on effective group membership, delegation and the permissions assigned to service identities.

## Checks

- Compare privileged group membership and delegated rights with the approved access inventory.
- Document which service accounts require interactive sign-in, elevated rights or legacy authentication.
- Correlate sensitive role changes with directory audit events and their change tickets.

## Mitigation

Remove stale delegated access, scope service rights to their jobs and rotate affected credentials after exposure. Review changes with an account that has a documented role baseline.

## References

- [Authorization review](web-access-control.md)
- [Credential exposure prevention](secret-handling.md)
