
#  OpenQuake Docker images <img src="https://upload.wikimedia.org/wikipedia/commons/7/79/Docker_%28container_engine%29_logo.png" width="150px"> 


## End user documentation

The main documentation, intended for end users, is available under the [documentation area](../doc/installing/docker.md)


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
To create a development image use the following command:

```bash
$ docker build -t openquake/engine:dev -f Dockerfile.dev .
```

Please note that the nightly image is meant for testing purposes and not for production.

### Debug

It's possible to enter a container as `root`, for debug purposes, running

```bash
$ docker run -u 0 -t -i  openquake/engine:nightly /bin/bash
```

### Environment Variables
The Openquake image uses several environment variables 

LOCKDOWN

This environment variable is required and set to True to enable the webui authentication. 
The default value is False, and it can also be undefined if the webui authentication is not necessary

```bash
$ docker run -e LOCKDOWN=True openquake/engine:nightly
```
If you don don set any other environment variables the default values for admin login, password and email are: 'admin', 'admin', 'admin@example.com'


OQ_ADMIN_LOGIN

This variable defines the superuser admin login in the webui 

OQ_ADMIN_PASSWORD

This environment variable sets the superuser admin password for webui

OQ_ADMIN_EMAIL

This environment variable sets the superuser admin email for webui

WEBUI_PATHPREFIX

This variable ovverides the default prefix path (/engine) for the webui 

```bash
$ docker run --name openquake -p 127.0.0.1:8800:8800 -e LOCKDOWN=True -e OQ_ADMIN_LOGIN=example -e OQ_ADMIN_PASSWORD=example -e OQ_ADMIN_EMAIL=login@example.com openquake/engine:nightly
```

This example runs a container named openquake using the openquake/engine:nightly image and set the value for the environment variables. 

This binds port 8800 of the container to TCP port 8800 on 127.0.0.1 of the host machine, so the webui is reachable from host machine using the url: http://127.0.0.1:8800/engine

```bash
$ docker run --name openquake -p 127.0.0.1:8080:8800 -e LOCKDOWN=True -e WEBUI_PATHPREFIX='/path' openquake/engine:nightly
```

This example runs a container named openquake using the openquake/engine:nightly image and set the value for the environment variables. 

This binds port 8800 of the container to TCP port 8080 on 127.0.0.1 of the host machine, so the webui is reachable from host machine using the url: http://127.0.0.1:8080/path
