
#  OpenQuake Docker images <img src="https://upload.wikimedia.org/wikipedia/commons/7/79/Docker_%28container_engine%29_logo.png" width="150px">


### Build the OpenQuake Engine docker

```bash
$ docker build -t openquake/engine -f Dockerfile.engine .
```

### Custom build args

```bash
--build-arg oq_branch=master      ## oq-engine branch
```

### Testing the image

If you want to use the nightly build instead of the latest, the files are in the docker folder.
To create a development image using the TAG nightly use the following command:

```bash
$ docker build -t openquake/engine:nightly -f Dockerfile.dev .
```

Please note that the nightly image is meant for testing purposes and not for production.

### Debug

It's possible to enter a container as `root`, for debug purposes, running

```bash
$ docker run -u 0 -t -i  openquake/engine:nightly /bin/bash
```

## End user documentation

The main documentation, intended for end users, is available under the [documentation area](https://docs.openquake.org/.dev/oq-engine/update_docker_doc/manual/getting-started/installation-instructions/docker.html)


