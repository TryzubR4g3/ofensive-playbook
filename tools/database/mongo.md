# mongo / mongosh

MongoDB shell. Two binaries to know about:
- **`mongo`** — legacy shell shipped with `mongodb-org-shell` ≤ 5.x. JS REPL, dies in 6.0+.
- **`mongosh`** — modern shell, 6.0+ default. Same surface for read queries; some admin commands renamed.

Both speak the wire protocol and default to `mongodb://127.0.0.1:27017`. Use whichever the box has installed; you almost never bring your own.

## Commands Used

### Connect — default localhost, no auth
```bash
mongo
mongosh
```
Used on: **cmspit**

### Connect — custom host/port/db, optional auth
```bash
mongo --host 127.0.0.1 --port 27017
mongo --host $TARGET --port 27017 dbname
mongo "mongodb://user:pass@127.0.0.1:27017/dbname?authSource=admin"
```

### Quick non-interactive query (one-shot, useful in scripts)
```bash
mongo --quiet --eval "db.adminCommand('listDatabases').databases.forEach(d=>print(d.name))"
mongo dbname --quiet --eval "db.users.find().forEach(printjson)"
```

### List → walk databases and collections
```javascript
> show dbs
> use sudousersbak                       // [USED — cmspit]
> show collections
> db.user.find()                         // [USED — cmspit, leaked stux:p4ssw0rdhack3d!123]
> db.user.find().pretty()
> db.flag.find()
```
Used on: **cmspit**

### One-shot dump-everything one-liner
```javascript
db.adminCommand("listDatabases").databases.forEach(function(d){
  db = db.getSiblingDB(d.name);
  db.getCollectionNames().forEach(function(c){
    print("=== " + d.name + "." + c + " ===");
    db[c].find().forEach(printjson);
  });
});
```

### Query DSL highlights
```javascript
db.users.find({role:"admin"})
db.users.find({}, {name:1, password:1, _id:0})       // projection
db.users.find({password:{$exists:true}})              // filter
db.users.find({name:{$regex:"adm", $options:"i"}})    // regex
db.users.count()
db.users.stats()
```

### Server / auth state checks
```javascript
db.runCommand({connectionStatus:1})       // who am I, what roles
db.runCommand({getCmdLineOpts:1})         // launch flags (auth on/off)
db.adminCommand({listDatabases:1})        // root-listing
db.serverBuildInfo().version
```

## When `mongo` is bound to localhost

Tunnel from the foothold:
```bash
ssh -L 27017:127.0.0.1:27017 user@$TARGET
mongo --host 127.0.0.1 --port 27017
```
See [ssh-tunneling.md](../../exploits/pivot/ssh-tunneling.md).

## When `mongo` is missing on the box

Install pymongo on your attacker side (after tunnelling), or one-line on the box:
```bash
python3 -c "from pymongo import MongoClient; c=MongoClient('mongodb://127.0.0.1'); [print(d) for d in c.list_database_names()]"
```

## Common gotchas

- `mongosh` (6.x+) deprecated `db.collection.count()` -- use `countDocuments({})`.
- `mongosh --eval` returns a JS object; chain `JSON.stringify(...)` for clean stdout.
- BSON `ObjectId` doesn't print on raw `print(...)` -- use `printjson` or `.toString()`.

## Related
- [mongodb-enumeration.md](../../exploits/creds/mongodb-enumeration.md) -- the playbook
- [cockpit-cms-rce.md](../../exploits/web-rce/cockpit-cms-rce.md) -- cmspit's foothold that fed into the mongo dump
- [ssh-tunneling.md](../../exploits/pivot/ssh-tunneling.md) -- when mongo is loopback only
- [linux-enumeration.md](../../exploits/enumeration/linux-enumeration.md) -- spotting mongod in `ss -tlnp` / `ps`
