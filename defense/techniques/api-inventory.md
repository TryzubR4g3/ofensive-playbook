# API route and version inventory

<!-- tags: API, API9:2023, unused endpoint, shadow API, OpenAPI, HTTP methods -->

Deployed operations outside an API inventory can miss access controls, maintenance and retirement.

## Signals

- Gateway routes, application routes and the published contract disagree about a method, path or version.
- Telemetry still shows requests reaching a retired API.
- A deployed operation lacks a named owner, documented audience or end-of-support date.

## Mitigation

Maintain an inventory by method, route, version, audience and environment. Compare the contract with deployed routes in CI and assign owners for differences. Remove obsolete routes from the gateway and the service. Use telemetry to confirm the change.

## References

- [OWASP API9:2023](https://api-security.owasp.org/editions/2023/en/0xa9-improper-inventory-management/)
- [API function-level authorization](api-function-authorization.md)
- [API review playbook](../playbooks/api-security-review.md)
