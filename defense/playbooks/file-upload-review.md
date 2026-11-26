# File upload security review

<!-- tags: web, file upload, storage, allowlist, audit, CWE-434 -->

Verify authorization, file validation, storage and delivery for each upload feature.

## Checks

1. Document accepted formats, size limits and permissions. Identify the component that stores files and the component that serves them.
2. Use inert test fixtures to confirm that required formats are accepted and unapproved formats are rejected.
3. Inspect configuration and infrastructure for write access outside upload storage and execution rights in the delivery path.
4. Verify download access and response headers. Log the upload ID, result and reason while keeping file contents out of logs.
5. Preserve evidence for each finding and add a regression case for the corrected control.

## References

- [File upload validation and isolation](../techniques/file-upload.md)
- [OWASP File Upload Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html)
