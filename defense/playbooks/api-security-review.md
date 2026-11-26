# API security review

<!-- tags: API, OpenAPI, Swagger, gateway, inventory, authorization, mass assignment, parameter pollution, API3:2023, API5:2023, API9:2023 -->

Use the API contract, service code and logs to verify operation permissions, writable fields and deployment consistency.

## Inputs

Collect the OpenAPI contract, gateway routes, permission matrix, request schemas and test logs produced with synthetic data.

## Checks

1. Compare the method, route and version in the contract with the deployed inventory. Assign an owner to each difference.
2. Compare the permission matrix with each sensitive operation. In an integration test, check both the response code and persisted state when a role is denied.
3. Confirm that each write schema lists the accepted fields and that server-owned values are set by the service.
4. Verify that internal HTTP clients use structured serialization and apply the same cardinality rules as the gateway.
5. Record the control, redacted evidence, owner and regression test for each finding.

## References

- [Mass assignment](../techniques/api-mass-assignment.md)
- [Function-level authorization](../techniques/api-function-authorization.md)
- [API inventory](../techniques/api-inventory.md)
- [Parameter pollution](../techniques/api-parameter-pollution.md)
- [Spectral contract checks](../tools/spectral.md)
- [Burp Suite captured traffic review](../tools/burp-http-history.md)
