# vulnnetroasted

<!-- brain:report -->
- **Platform** TryHackMe
- **Difficulty** Easy
- **Source status** Limited detail

## Report overview

The observations in this case inform a review of service and share exposure and evidence and artifact review.

## Defensive takeaways

- Confirm the intended audience for network services and shares, then compare their permissions and reachability with that policy.
- Record the source and timestamp of observed evidence and mark unverified conclusions separately.

## Defensive references

- [Exposed service and share hardening](../../../defense/techniques/service-exposure-review.md)
- [Evidence handling and artifact review](../../../defense/techniques/evidence-handling.md)

<!-- /brain:report -->

---


## Reconnaissance
```bash
silent-scan $TARGET
nmap -sVC -p53,88,135,139,389,445,464,593,636,3268,3269,5985,9389,49666,49668,49669,49670,49673,49710 $TARGET -oN service
```

