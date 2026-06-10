# Time-Based Blind SQL Injection

Used on: **SQL Injection Fundamentals**

Time-based blind SQLi is used when there is no visible true/false difference in the response. The signal becomes response time: if the condition is true, the database sleeps before returning.

## When to Use

- The application response does not visibly change when true or false conditions are injected.
- Injecting a delay function (e.g., `SLEEP(5)`) causes the HTTP response to take noticeably longer.
- Network latency is stable enough to reliably distinguish between normal and delayed responses.

## Prerequisites

- A vulnerable parameter affects a SQL query.
- The database supports a delay function such as `SLEEP()`.
- Network latency is stable enough to distinguish normal responses from delayed responses.

## Steps

### 1. Find the column count

<!-- cmd: sql -->
```sql
admin123' UNION SELECT SLEEP(5);--
admin123' UNION SELECT SLEEP(5),2;--
```

The payload that produces a delay has the correct `UNION SELECT` shape.

### 2. Enumerate the database name

<!-- cmd: sql -->
```sql
admin123' UNION SELECT SLEEP(5),2 WHERE database() LIKE 'u%';--
```

A five-second delay means the condition is true. Continue prefix testing until the name is complete.

### 3. Reuse the boolean-based workflow

The rest of the process mirrors boolean-based SQLi, replacing the true/false page signal with a delay:

1. Column count with `UNION SELECT SLEEP(5), ...`
2. Database name with `WHERE database() LIKE 'x%'`
3. Table names through `information_schema.tables`
4. Column names through `information_schema.COLUMNS`
5. Usernames and passwords through table-specific `LIKE` predicates

## Boolean vs Time-Based

| Boolean-Based | Time-Based |
|----------------|------------|
| Response visibly changes | Response time changes |
| Faster to enumerate | Slower and noisier |
| Needs a stable content signal | Needs stable latency |

## Defensive Note

Parameterized queries are the fix. Adding generic responses or suppressing SQL errors does not remove the injection; time delays can still leak data.