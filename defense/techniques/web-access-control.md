# Web authorization and account recovery

<!-- tags: web authorization, access control, account recovery, password reset, IDOR, authentication, role matrix -->

Review permissions per action and resource, along with the controls that govern account recovery.

## Checks

- Compare server-side authorization to a documented role and resource matrix.
- Confirm account recovery verifies the requester and invalidates used or expired recovery tokens.
- Check integration tests for denied actions and unchanged persisted state.

## Mitigation

Centralize authorization decisions, scope them to the requested action and resource, and enforce them in the service. Use single-use recovery tokens and audit recovery events.

## References

- [OWASP authorization guidance](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)
- [API function-level authorization](api-function-authorization.md)
