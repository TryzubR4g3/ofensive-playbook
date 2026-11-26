# Spectral for OpenAPI review

<!-- tags: API, OpenAPI, Swagger, linter, YAML, JSON, CI, inventory -->

Spectral checks API definitions against static rules before deployment.

## Review workflow

With Spectral installed and a local `.spectral.yaml` extending `spectral:oas`, run the linter against the versioned contract from the service directory.

<!-- cmd: cross-platform -->
```bash
spectral lint openapi.yaml --ruleset .spectral.yaml
```

Pair contract linting with a deployed-route inventory and server-side authorization tests.

## References

- [Spectral OpenAPI rules](https://github.com/stoplightio/spectral/blob/develop/docs/reference/openapi-rules.md)
- [API review playbook](../playbooks/api-security-review.md)
