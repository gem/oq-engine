# OpenQuake Docker images

<img src="https://upload.wikimedia.org/wikipedia/commons/7/79/Docker_%28container_engine%29_logo.png" width="150px"> [![Build Status](https://ci.openquake.org/buildStatus/icon?job=builders/docker-builder)](https://ci.openquake.org/job/builders/docker-builder)

End user documentation: ../doc/installing/docker.md


## Python3 base image (required by all images)

```bash
$ docker build -t openquake/base -f Dockerfile.base .
```

## OpenQuake Engine (single node)

```bash
$ docker build -t openquake/engine -f Dockerfile.engine .
```

## OpenQuake Engine master node container (cluster)

```bash
$ docker build -t openquake/engine-master -f Dockerfile.master .
```

## OpenQuake Engine worker node container (cluster)

```bash
$ docker build -t openquake/engine-worker -f Dockerfile.worker .
```

## Custom build args

```bash
--build-arg oq_branch=master      ## oq-engine branch
--build-arg tools_branch=mater    ## oq standalone tools branch
```

## Debug

It's possible to enter a container as `root`, for debug purposes, running

```bash
$ docker exec -u 0 -t -i oq-cluster-master /bin/bash
```
