# borderlands

## Reconnaice
```bash
silent-scan $TARGET
nmap -sVC -p22,80 $TARGET -oN service
```

**Output**
```
22/tcp open  ssh     OpenSSH 7.2p2 Ubuntu 4ubuntu2.8 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   2048 0f:9c:f3:31:fc:bd:54:34:23:18:d1:0d:f8:8c:a2:fa (RSA)
|   256 3c:9d:cd:c6:ed:6f:fd:86:8f:09:a1:3a:ad:d7:26:e3 (ECDSA)
|_  256 a5:83:c4:d4:fb:39:5b:23:1b:f3:00:88:a7:49:74:6e (ED25519)
80/tcp open  http    nginx 1.14.0 (Ubuntu)
|_http-title: Context Information Security - HackBack 2
|_http-server-header: nginx/1.14.0 (Ubuntu)
| http-cookie-flags: 
|   /: 
|     PHPSESSID: 
|_      httponly flag not set
| http-git: 
|   10.130.161.204:80/.git/
|     Git repository found!
|     .git/config matched patterns 'user'
|     Repository description: Unnamed repository; edit this file 'description' to name the.
```

## Web Fuzzing 

### We already find a .git repo with the nmap script
### So let's take a look and fuzz the http service
```bash
feroxbuster -u http://$TARGET -w /usr/share/wordlists/dirb/common.txt
```
**Output**
```bash
00      GET        1l        2w       23c http://10.130.161.204/.git/HEAD
200      GET      364l     2694w    89151c http://10.130.161.204/Context_White_Paper_Pen_Test_101.pdf
200      GET     2292l    14163w   943202c http://10.130.161.204/CTX_WSUSpect_White_Paper.pdf
200      GET     3965l    21467w  1412748c http://10.130.161.204/Context_Red_Teaming_Guide.pdf
200      GET        9l       85w    15227c http://10.130.161.204/index.php
200      GET     5158l    80691w  1610299c http://10.130.161.204/Glibc_Adventures-The_Forgotten_Chunks.pdf
200      GET      928l     4779w    80541c http://10.130.161.204/info.php
200      GET     7887l    42576w  3866144c http://10.130.161.204/mobile-app-prototype.apk
200      GET     8103l    37557w  3428529c http://10.130.161.204/Demystifying_the_Exploit_Kit_-_Context_White_Paper.pdf
```

### Let's reverse the apk 
```bash
# unzip the apk
unzip mobile-app-prototype.apk -d app_source
jadx-gui classes.dex
# Decode full apk
apktool d nombre_del_apk.apk -o output_folder/
# Search for the api_key
grep -r "encrypted_api_key" .
```
### We can apreciate in the original code with jadx that api key is encrypetd with a personalized encryption
```bash
 this.apiKey = decrypt(getString(C0228R.string.encrypted_api_key), "#TODO");
        this.apiPath = "/api.php?documentid={}&apikey=" + this.apiKey
```
**Output**
```
./res/values/strings.xml:    <string name="encrypted_api_key">CBQOSTEFZNL5U8LJB2hhBTDvQi2zQo</string>
```



