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

### Testing the image
To create a development image use the following command:

```bash
$ docker build -t openquake/engine:dev -f Dockerfile.dev .
```

### Testing
If you want to use the nightly build instead of the latest, the files are in the docker folder.

Please note that the nightly image is meant for testing purposes and not for production.

### Debug

It's possible to enter a container as `root`, for debug purposes, running

```bash
$ docker run -u 0 -t -i  openquake/engine:nightly /bin/bash
```
