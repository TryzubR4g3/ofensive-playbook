# httrack

Website copier. Used to mirror entire sites locally for offline analysis — useful for
extracting embedded emails, usernames, image filenames, and other OSINT artefacts that
are hard to spot while browsing interactively.

## Commands Used

### Mirror a site and extract email addresses

```bash
httrack "http://fire.windcorp.thm" -o /tmp/windcorp
grep -r "@fire.windcorp.thm" /tmp/windcorp --include="*.html" -h \
  | grep -o '[a-zA-Z0-9._-]*@fire\.windcorp\.thm' | sort -u
```

Used on: **Ra**

Cloned `fire.windcorp.thm` to extract every embedded email address from the corporate
site HTML — produced a full domain user list for XMPP targeting.

## Notes

- `-o <dir>` — output directory (created if absent)
- By default httrack follows all links on the target domain
- Combine with `grep -r` for bulk extraction of patterns (emails, usernames, paths)
- Works well when `ffuf`/`gobuster` finds no high-value paths but the page source has
  embedded data
