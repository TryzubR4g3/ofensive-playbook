# Exposed service and share hardening

<!-- tags: service exposure, SMB, Samba, NFS, FTP, WebDAV, Telnet, DNS, file shares, anonymous access -->

Review the network reachability and access policy of file shares, management services and supporting protocols.

## Checks

- Compare listening services with their required audiences and assigned owners.
- Review anonymous access, share permissions and management interfaces against policy.
- Confirm legacy protocols have an explicit exception, limited reachability and a replacement plan.

## Mitigation

Disable unused services, limit network reachability and require scoped identities for access. Record share and service changes and recheck intended access after remediation.

## References

- [Network segmentation review](network-segmentation.md)
- [Credential exposure prevention](secret-handling.md)
