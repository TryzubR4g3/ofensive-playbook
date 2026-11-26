# Input validation and interpreter boundaries

<!-- tags: input validation, SQL injection, SQLi, XSS, XXE, SSRF, file inclusion, injection, path traversal, templating, deserialization -->

Review boundaries where untrusted data reaches queries, templates, files, parsers or outbound requests.

## Checks

- Find the component that converts input into an operation and inspect the interface it uses.
- Check that schema validation and canonicalization happen before the relevant policy decision.
- Confirm error handling and logs preserve enough context for investigation without disclosing secrets.

## Mitigation

Use structured APIs such as parameterized database queries and context-aware template escaping. Restrict filesystem and network access to what the service requires. Add focused regression tests with synthetic inputs for each boundary.

## References

- [OWASP input validation guidance](https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html)
- [API parameter pollution](api-parameter-pollution.md)
