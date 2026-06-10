# showmount

RPC-based NFS export lister. Queries the mount daemon to list which directories the server exports, and to which clients. Run first whenever ports 111 / 2049 are open.

## Commands Used

### List all exports
<!-- cmd: linux -->
```bash
showmount -e $TARGET
```
Used on: **VulnNet: Internal**

revealed `/opt/conf *` (world-mountable).

### Useful variations
<!-- cmd: linux -->
```bash
showmount -a $TARGET     # active client mounts
showmount -d $TARGET     # directories currently mounted by clients
```

## Pairing with actual mount

<!-- cmd: linux -->
```bash
sudo mkdir -p /mnt/nfs_target
sudo mount -t nfs $TARGET:/opt/conf /mnt/nfs_target
# troubleshooting fallback:
sudo mount -t nfs -o vers=3,nolock,soft $TARGET:/opt/conf /mnt/nfs_target
```

## Nmap NSE alternatives

If `showmount` is blocked but `mountd` still responds:
<!-- cmd: linux -->
```bash
nmap -sV -p111,2049 --script nfs-ls,nfs-showmount,nfs-statfs $TARGET
```

## Related
- [NFS share abuse playbook](../../exploits/network-services/nfs-share-abuse.md)


