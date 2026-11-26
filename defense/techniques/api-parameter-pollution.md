# Server-side parameter pollution

<!-- tags: API, server-side parameter pollution, SSPP, HTTP parameter pollution, query string, CWE-235 -->

When an application constructs an internal request, client-provided values can be interpreted as part of the request's parameter structure.

## Signals

- An internal HTTP client builds a query string by concatenating request data.
- The gateway and the internal service handle repeated fields differently.
- Serializer tests show keys outside the contract after a request is constructed.

## Mitigation

Use an HTTP serializer with fixed parameter names and typed values. Define cardinality per field and reject ambiguous input at validation. Assert the resulting keys with synthetic request fixtures.

## References

- [MITRE CWE-235 for duplicate parameters](https://cwe.mitre.org/data/definitions/235.html)
- [API review playbook](../playbooks/api-security-review.md)
