# Mythical

<!-- brain:report -->
- **Platform** Hack The Box
- **Source status** Documented

## Report overview

The observations in this case inform a review of directory identity and delegation and network segmentation.

## Defensive takeaways

- Audit effective group membership, service identities and delegated rights against the approved access baseline.
- Compare cross-zone routes with the dependency map and audit access to management systems.

## Defensive references

- [Directory identity and delegated access review](../../../defense/techniques/directory-access-review.md)
- [Network segmentation and trust boundaries](../../../defense/techniques/network-segmentation.md)

<!-- /brain:report -->

---

## Description
```
Introduction

You are tasked with performing a red team engagement on Mythical Inc. The company does not allow data leaving the internal network, so a c2 server has been set up internally and an employee executed a payload in order to simulate a successful social engineering attack.Use the following credentials to login into the web interface of the Mythic c2 server on port 7443:mythic_admin:wG4jmjNcEcfmzv3QbEcJdSVTDEjCnX

Mythical is a small active directory scenario in which you start with an already running Mythic C2 beacon on an internal system. It is designed to practice operating through a C2 framework in a modern, challenging windows environment.

Mythical is designed for penetration testers and red teamers in search of a quick and challenging lab that has c2 infrastructure already set up in order to practice c2 operations.

This Red Team Operator I lab will expose players to:

    Enumeration
    Active Directory enumeration and attacks
    Active Directory Certificate Services
    Lateral movement
    Local privilege escalation
    Situational awareness
    MSSQL attacks
    C2 Operations
```

