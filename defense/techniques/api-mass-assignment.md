# API mass assignment

<!-- tags: API, mass assignment, autobinding, BOPLA, CWE-915, API3:2023 -->

Automatic binding can let request data reach model properties that the server should control.

## Signals

- The handler deserializes requests directly into a persisted model.
- An input schema accepts internal authorization, state or business fields.
- An audit record shows a property change outside the actor's expected permissions.

## Mitigation

Define an input schema per operation and list its writable fields and types. Check permission to write sensitive properties and set server-owned values in the service. Add a regression test that verifies denied changes leave persisted state intact.

## References

- [OWASP API3:2023](https://api-security.owasp.org/editions/2023/en/0xa3-broken-object-property-level-authorization/)
- [MITRE CWE-915](https://cwe.mitre.org/data/definitions/915.html)
- [API review playbook](../playbooks/api-security-review.md)
