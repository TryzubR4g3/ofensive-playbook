# File upload validation and isolation

<!-- tags: web, file upload, upload security, allowlist, blacklist, CWE-434 -->

File uploads need format validation, isolated storage and an explicit access policy for retrieval.

## Signals

- The application trusts only filename extensions or client-declared metadata.
- The upload service can write to a code or configuration directory.
- A web server or interpreter treats files in the upload location as executable.

## Mitigation

Allow the smallest set of required formats and validate content with a maintained parser. Assign server-generated filenames. Store data outside the webroot or in isolated object storage and serve it without code execution. Authorize uploads and downloads separately.

## References

- [OWASP File Upload Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html)
- [MITRE CWE-434](https://cwe.mitre.org/data/definitions/434.html)
- [File upload review playbook](../playbooks/file-upload-review.md)
