# Evidence handling and artifact review

<!-- tags: forensics, evidence, artifacts, packet capture, metadata, Wireshark, logs, redaction -->

Document observed behavior using artifacts with a clear source, timestamp and review scope.

## Checks

- Record the acquisition source and keep a read-only copy of the original.
- Label observations, interpretations and unverified claims separately.
- Redact sensitive fields from shared excerpts and retain needed context in the restricted original.

## Workflow

Store restricted evidence with the corresponding case. Use reproducible review tools and record their versions where the interpretation depends on the parser. Add links to supporting control notes once the observation is confirmed.

## References

- [Credential exposure prevention](secret-handling.md)
- [API security review](../playbooks/api-security-review.md)
- [Wireshark for offline evidence review](../tools/wireshark.md)
