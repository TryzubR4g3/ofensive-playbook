# PowerView

PowerShell tool to gain network situational awareness on Windows domains. It is part of the PowerSploit project and provides a set of cmdlets to query Active Directory.

## Commands Used

### Enumerate Object ACLs
```powershell
upload /usr/share/powershell-empire/.../powerview.ps1
. .\PowerView.ps1

Get-DomainObjectAcl -ResolveGUIDs | Where-Object {
  $_.SecurityIdentifier -eq (Get-DomainUser j.harris).objectsid
}
```
Used on: **dead-drop**

Found that the user `j.harris` had `Self-Membership` (AddSelf) permissions over the `ITSupport-Admins` group, which was nested into `Domain Admins`.

## Notes
- To bypass execution policies: `powershell -ep bypass`
- `Get-DomainObjectAcl` is extremely useful for discovering misconfigured permissions on AD objects.
- `-ResolveGUIDs` helps by replacing raw GUIDs in ACLs with readable display names.
