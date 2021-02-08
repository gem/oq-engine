# OpenQuake Docker images

<img src="https://upload.wikimedia.org/wikipedia/commons/7/79/Docker_%28container_engine%29_logo.png" width="150px"> [![Build Status](https://ci.openquake.org/buildStatus/icon?job=builders/docker-builder)](https://ci.openquake.org/job/builders/docker-builder)

## End user documentation

The main documentation, intended for end users, is available under the [documentation area](../doc/installing/docker.md)


### OpenQuake Engine (single node)

```bash
$ docker build -t openquake/engine -f Dockerfile.engine .
```

### Custom build args

```bash
--build-arg oq_branch=master      ## oq-engine branch
```

### Testing image
To have a development image use the follow Dockerfile to have into the image also the source code and the developer installation of engine.

```bash
$ docker build -t openquake/engine:dev -f Dockerfile.dev .
```

## Master/worker images (clustered setup)

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

The files that compose the infrastructure for ZMQ are available on zmq subfolder of docker folder and use the latest tag

You need to be on that folder to use the follow commands:

```bash
$ docker-compose -f docker-compose.yml <build,up,down...> 
```

If you want more to scale the worker service start with follow:
```bash
$ docker-compose -f docker-compose.yml <build,up,down...> --scale worker=NUM

```
### Testing
If you want to use the nightly build instead of the latest all the files are in the docker folder.

Please note that the nightly image and also the configuration files in that folder are only for testing pourpose and not use in  production environment.

### Debug

It's possible to enter a container as `root`, for debug purposes, running

```bash
$ docker exec -u 0 -t -i engine-master /bin/bash
```
