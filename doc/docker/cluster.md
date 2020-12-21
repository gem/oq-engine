# Docker cluster deployment

## Cluster deployment

For a clustered multi node deployment an orchestrator like [Kubernetes](https://kubernetes.io/) or [Swarm](https://docs.docker.com/engine/swarm/) is recommended.
As a _reference_ a Docker compose is included. It creates an OpenQuake Engine cluster with **dynamic scaling capabilities**:

```bash
$ docker-compose  up
```

Containers can be also started in background using `$ docker-compose up -d`.

More workers can be started via

```bash
$ docker-compose  up --scale worker=N
```
where `N` is the number of expected worker containers.


### Shared directory

Starting with the OpenQuake Engine 3.3 a [shared directory](../installing/cluster.md) must exists between the master node and workers. Docker compose already set a shared volume between containers ([docker-compose.yml#L9](../../docker/docker-compose.yml#L9)).
When running containers on different hosts (which should be the case) you must adjust `docker-compose.yml` properly to use a shared storage backend.
A configuration example for NFS is provided via the `oqdata-nfs` volume in [docker-compose.yml#L10](../../docker/docker-compose.yml#L10).

### Docker

- [Introduction](../installing/docker.md)
- [Single node deployment](single.md)
- [Advanced options](advanced.md)

***

## Getting help
If you need help or have questions/comments/feedback for us, you can:
  * Subscribe to the OpenQuake users mailing list: https://groups.google.com/g/openquake-users
  * Contact us on IRC: irc.freenode.net, channel #openquake
