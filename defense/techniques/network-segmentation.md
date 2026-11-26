# Network segmentation and trust boundaries

<!-- tags: network segmentation, routing, firewall, internal network, jump host, boundary review -->

Review which systems can initiate connections across internal zones and how that access is monitored.

## Checks

- Compare permitted ingress and egress with a documented application dependency map.
- Identify management interfaces and routes that cross an environment or organizational boundary.
- Confirm logs record the decision and owner for cross-zone connection policies.

## Mitigation

Apply narrowly scoped network policies and require authenticated administrative access. Remove undocumented exceptions and verify expected connection paths after changes.

## References

- [Exposed service hardening](service-exposure-review.md)
- [Directory identity review](directory-access-review.md)
