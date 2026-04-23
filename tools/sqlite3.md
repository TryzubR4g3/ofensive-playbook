# sqlite3 / db_dump (Berkeley DB)

Two small tools for handling the `.db` files that keep surfacing during web-app loot: **sqlite3** for SQLite 3 databases, and **db_dump** (from `db-util` / `libdb-utils`) for Berkeley DB files. They look identical from the outside — the first move is always `file <x>.db` to decide which one to reach for.

## Commands Used

### Decide what format the file is
```bash
file cache.db
# cache.db: SQLite 3.x database, last written using SQLite version ...
#   OR
# cache.db: Berkeley DB (Hash, version 9, native byte-order)
```
Used on: **LazyAdmin** — `cache.db` from `/content/inc/cache/cache.db` was Berkeley DB, not SQLite.

### SQLite 3
```bash
sqlite3 cache.db
sqlite> .tables
sqlite> .schema <table>
sqlite> SELECT * FROM <table>;
sqlite> .dump                     # full SQL dump to stdout
sqlite> .exit
```

One-shot forms:
```bash
sqlite3 cache.db '.tables'
sqlite3 cache.db '.dump' > cache.sql
sqlite3 cache.db "SELECT name, password FROM users;"
```

### Berkeley DB (`db_dump`)
```bash
sudo apt-get install db-util          # provides db_dump, db_load, db_stat
db_dump -p cache.db                   # [USED — LazyAdmin] — printable dump
db_dump cache.db                      # raw dump (binary-safe)
db_stat -d cache.db                   # DB type + page stats
```

LazyAdmin's `cache.db` dumped to a list of `db_array_<md5>` keys mapped to timestamps — the interesting data was elsewhere (the SQL backups), but `db_dump` was the right tool to confirm there were no credentials inside.

### Other common `.db` surprises
- **DBM / GDBM** (rare) — `gdbm_dump` if available, otherwise `strings` will give you the contents most of the time.
- **MS SQL CE / Jet** — `.db` from .NET apps; treat as opaque, extract with `strings`.
- **LevelDB / RocksDB** — whole directory of `.ldb` files, not a single `.db`; use `plyvel` (Python) if you need real access.

## Grepping dumps for credentials
```bash
db_dump -p cache.db | grep -Ei 'pass|hash|user|token'
sqlite3 cache.db '.dump' | grep -Ei 'pass|hash|user|token'
```

## Related
- [backup-file-exposure.md](../exploits/backup-file-exposure.md) — where `.db` and `.sql` files usually come from
- [strings](strings.md) — last-resort fallback for unknown binary DBs
