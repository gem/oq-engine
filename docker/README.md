# OpenQuake Docker images

<img src="https://upload.wikimedia.org/wikipedia/commons/7/79/Docker_%28container_engine%29_logo.png" width="150px"> [![Build Status](https://ci.openquake.org/buildStatus/icon?job=builders/docker-builder)](https://ci.openquake.org/job/builders/docker-builder)

## End user documentation

The main documentation, intended for end users, is available under the [documentation area](../doc/installing/docker.md)


## Images

Images are based on **CentOS 8**

### Python3 base image (required by all images)

```bash
$ docker build -t openquake/base -f Dockerfile.base .
```

### OpenQuake Engine (single node)

```bash
$ docker build -t openquake/engine -f Dockerfile.engine .
```

### Custom build args

```bash
--build-arg oq_branch=master      ## oq-engine branch
--build-arg tools_branch=mater    ## oq standalone tools branch
```


## Master/worker images (clustered setup)

### OpenQuake Engine master node container (celery)

```bash
$ docker build -t openquake/engine-master-celery -f celery/Dockerfile.master .
```

### OpenQuake Engine worker node container (celery)

```bash
$ docker build -t openquake/engine-worker-celery -f celery/Dockerfile.worker .
```

### OpenQuake Engine master node container (zmq)

```bash
$ docker build -t openquake/engine-master-zmq -f zmq/Dockerfile.master .
```

### OpenQuake Engine worker node container (zmq)

```bash
$ docker build -t openquake/engine-worker-zmq -f zmq/Dockerfile.worker .
```

## Master/worker images (clustered setup) via 'docker-compose'

### ZMQ

```bash
$ docker-compose -f docker-compose.yml <build,up,down...> [--scale worker=N]
```

### Celery

```bash
$ docker-compose -f docker-compose.yml -f docker-compose.celery.yml <build,up,down...> [--scale worker=N]
```

### Debug

It's possible to enter a container as `root`, for debug purposes, running

```bash
$ docker exec -u 0 -t -i oq-cluster-master /bin/bash
```
