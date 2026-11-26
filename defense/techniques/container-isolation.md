# Container runtime and workload isolation

<!-- tags: Docker, containers, Kubernetes, runtime socket, workload identity, mounts, capabilities -->

Review the boundary between a container workload, the host and the container runtime.

## Checks

- Compare runtime access, mounts, workload identities and elevated capabilities with the deployment policy.
- Verify that persistent storage and host interfaces have documented owners and narrowly scoped access.
- Review image provenance and cleanup for unused workload permissions.

## Mitigation

Keep control-plane interfaces restricted to their management identities. Remove unnecessary privileges, host access and writable mounts. Enforce approved workload settings at deployment time.

## References

- [Unix host privilege review](host-privilege-review.md)
- [Network segmentation review](network-segmentation.md)
