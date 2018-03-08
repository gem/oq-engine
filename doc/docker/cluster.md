# Docker cluster deployment

## Cluster deployment

For a clustered multi node deployment an orchestrator like [Kubernetes](https://kubernetes.io/) or [Swarm](https://docs.docker.com/engine/swarm/) is recommended.
As a _reference_ a Docker compose is included. It creates an OpenQuake Engine cluster with **dynamic scaling capabilities**:

```bash
$ docker-compose up
```

Containers can be also started in background using `$ docker-compose up -d`.

More workers can be started via

```bash
$ docker-compose up --scale worker=N
```
where `N` is the number of expected worker containers.

## Deploy an OpenQuake Engine cluster manually

### OQ internal network

```bash
$ docker network create --driver bridge oq-cluster-net
```

### RabbitMQ container

```bash
$ docker run -d --network=oq-cluster-net --name oq-cluster-rabbit -e RABBITMQ_DEFAULT_VHOST=openquake -e RABBITMQ_DEFAULT_USER=openquake -e RABBITMQ_DEFAULT_PASS=openquake rabbitmq:3
```

### Master node container

```bash
$ docker run -d --network=oq-cluster-net --name oq-cluster-master -p8800:8800 openquake/engine-master
```

### Worker nodes

```bash
$ docker run -d --network=oq-cluster-net --name oq-cluster-worker_1 openquake/engine-worker
```

### Docker

- [Introduction](../installing/docker.md)
- [Single node deployment](single.md)
- [Advanced options](advanced.md)
- [Build from sources](https://github.com/gem/oq-builders/tree/master/oq-docker#build-openquake-docker-images)

***

## Getting help
If you need help or have questions/comments/feedback for us, you can:
  * Subscribe to the OpenQuake users mailing list: https://groups.google.com/forum/?fromgroups#!forum/openquake-users
  * Contact us on IRC: irc.freenode.net, channel #openquake
