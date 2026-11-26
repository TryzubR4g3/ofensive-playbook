# API function-level authorization

<!-- tags: API, broken function level authorization, BFLA, API5:2023, OpenAPI, Swagger, interactive documentation, CWE-285 -->

Each API operation needs server-side authorization, including administrative actions shown in interactive documentation.

## Signals

- The API requires authentication globally and lacks explicit permissions for sensitive operations.
- HTTP methods on the same route use different or incomplete access policies.
- An audit record shows a sensitive action the service's permission matrix does not allow for that role.

## Mitigation

Deny access by default and assign explicit permissions to each route and method combination. Enforce those permissions in every deployed version. Scope access to interactive documentation to its audience and verify each documented operation independently.

## References

- [OWASP API5:2023](https://api-security.owasp.org/editions/2023/en/0xa5-broken-function-level-authorization/)
- [API review playbook](../playbooks/api-security-review.md)
