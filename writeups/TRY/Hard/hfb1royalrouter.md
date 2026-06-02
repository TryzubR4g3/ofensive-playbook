# hfb1royalrouter

## Recon

```bash
silent-scan $TARGET
nmap -sVC -p22,23,80,9999,20443,24433,28080,50628 $TARGET -oN service
nmap -sU -p- -n -Pn --min-rate 2000 $TARGET --open -oN udp-top-2000
```

**Output**
```
PORT      STATE SERVICE    VERSION
22/tcp    open  ssh        OpenSSH 8.9p1 Ubuntu 3ubuntu0.13 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   256 aa:a7:c2:3d:6d:b0:b3:69:0e:7f:52:04:98:53:8f:2a (ECDSA)
|_  256 0b:46:40:21:9a:8e:e2:3d:5e:1d:7b:ba:16:8f:6e:b3 (ED25519)
23/tcp    open  tcpwrapped
80/tcp    open  tcpwrapped
9999/tcp  open  tcpwrapped
20443/tcp open  tcpwrapped
24433/tcp open  tcpwrapped
28080/tcp open  tcpwrapped
50628/tcp open  tcpwrapped
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel
```

## Related Notes

- [nmap](../../../tools/recon/nmap.md)






