# WordPress wp-config.php Credential Reuse

Used on: **Internal**

WordPress database credentials in `wp-config.php` are often useful for local database access and sometimes lead to reused system credentials elsewhere on the host.

## Prerequisites

- File read access as the web server user or better.
- WordPress installation path known.

## Steps

Extract database configuration:

```bash
cat /var/www/html/wordpress/wp-config.php | grep -E "DB_|host|port"
```

Try local MySQL access:

```bash
mysql -h localhost -u wordpress -pwordpress123 wordpress
```

Continue manual local enumeration when the database does not contain the next pivot:

```bash
cd /opt/
ls -lha
cat wp-save.txt
```

## Defensive Note

Use unique DB passwords, restrict file permissions, and never store human account credentials in world-readable operational notes.

## Related

- [../enumeration/linux-enumeration.md](../enumeration/linux-enumeration.md)


