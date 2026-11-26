# Burp Suite HTTP history for traffic review

<!-- tags: API, Burp Suite, proxy, HTTP history, capture, logs, traffic -->

HTTP history records requests and responses that passed through Burp Proxy so QA traffic can be compared with the expected contract.

## Review workflow

1. Open HTTP history from an approved QA session and filter by host and method.
2. Compare the method, route and response status with the contract. Check unexpected authorization outcomes against service logs.
3. Redact cookies, tokens, personal data and unneeded request bodies before recording evidence.

## References

- [PortSwigger HTTP history](https://portswigger.net/burp/documentation/desktop/tools/proxy/http-history)
- [API review playbook](../playbooks/api-security-review.md)
