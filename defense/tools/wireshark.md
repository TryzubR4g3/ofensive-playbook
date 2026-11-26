# Wireshark for offline evidence review

<!-- tags: Wireshark, PCAP, packet capture, forensics, traffic review, evidence -->

Use Wireshark to inspect a capture already collected for an incident or an authorized test.

## Review workflow

1. Work from a copy of the capture and record where the original is stored.
2. Identify the relevant time window and use display filters to focus on the connections under review.
3. Record frame numbers, timestamps and the part of the conversation that supports each observation.
4. Export only the frames needed for a finding and review the export for secrets or personal data.

## References

- [Wireshark User's Guide](https://www.wireshark.org/docs/wsug_html_chunked/ChIOOpenSection.html)
- [Evidence handling](../techniques/evidence-handling.md)
