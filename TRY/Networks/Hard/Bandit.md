# Bandit

**Estado:** WIP / pendiente de terminar.  
**Nota:** Se deja en espanol. Solo esta documentado el registro inicial y el primer escaneo.

ssh register@10.200.30.250

Thank you for registering, please take note of the following details. Your entry host for this challenge is 10.200.30.107.

## Recon
```bash
### silent scan
 nmap -sS -p- -n -Pn --min-rate 5000 $TARGET --open -oN silent
### service scan
```
