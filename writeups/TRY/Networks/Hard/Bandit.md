# Bandit

**Status:** WIP / incomplete.
**Note:** Only initial registration and first scan are documented.

ssh register@10.200.30.250

Thank you for registering, please take note of the following details. Your entry host for this challenge is 10.200.30.107.

## Recon
```bash
ping 10.200.30.101
ping 10.200.30.10
### silent scan
 nmap -sS -p- -n -Pn --min-rate 5000 -iL targets.txt --open -oN silent-targets
### service scan
nmap -sVC -p 22,80,631,8002 10.200.30.101 -oN service-10.200.30.101
nmap -sVC -p 135,139,445,3389,5985,47001,49664,49665,49666,49669,49670,49672,49673 10.200.30.10 -oN service-10.200.30.10
```

**Output**
```
10.200.30.101
PORT     STATE SERVICE            VERSION
22/tcp   open  ssh                OpenSSH 8.2p1 Ubuntu 4ubuntu0.5 (Ubuntu Linux; protocol 2.0)
80/tcp   open  http-proxy         Apache Traffic Server 7.1.1
|_http-title: Not Found on Accelerator
|_http-server-header: ATS/7.1.1
631/tcp  open  ipp                CUPS 2.4
|_http-server-header: CUPS/2.4 IPP/2.1
|_http-title: Forbidden - CUPS v2.4.5
8002/tcp open  hadoop-tasktracker Apache Hadoop

10.200.30.10
______________________________________________
PORT      STATE SERVICE       VERSION
135/tcp   open  msrpc         Microsoft Windows RPC
139/tcp   open  netbios-ssn   Microsoft Windows netbios-ssn
445/tcp   open  microsoft-ds
3389/tcp  open  ms-wbt-server Microsoft Terminal Services
5985/tcp  open  http          Microsoft HTTPAPI httpd 2.0 (SSDP/UPnP)
|_http-title: Not Found
|_http-server-header: Microsoft-HTTPAPI/2.0
47001/tcp open  http          Microsoft HTTPAPI httpd 2.0 (SSDP/UPnP)
49664/tcp open  msrpc         Microsoft Windows RPC
49665/tcp open  msrpc         Microsoft Windows RPC
49666/tcp open  msrpc         Microsoft Windows RPC
49669/tcp open  msrpc         Microsoft Windows RPC
49670/tcp open  msrpc         Microsoft Windows RPC
49672/tcp open  msrpc         Microsoft Windows RPC
49673/tcp open  msrpc         Microsoft Windows RPC
```

## Web Enumeration on 10.200.30.101:8002
```bash
feroxbuster -u http://10.200.30.101:8002 \
  -w /usr/share/wordlists/dirb/common.txt \
  -x php,js,env,conf,txt,html,json,config,bak,sql,db \
  -t 50 \
  -d 3 \
  --status-codes 200,201,301,302,403,405,500 \
  -o ferox-8002.txt
```
