# Docker advanced options

## Authentication support

Authentication support for the WebUI/API can be enabled passing the `LOCKDOWN` environment variable to the Docker container; it can be set to any value:

### Single container 

```bash
$ docker run -e LOCKDOWN=enabled --name myoqcontainer -d -p 8800:8800 openquake/engine
```

### Docker compose (cluster)

```bash
LOCKDOWN=enabled docker-compose up -d
```

### Docker

- [Introduction](../installing/docker.md)
- [Single node deployment](single.md)
- [Cluster deployment](cluster.md)
- [Build from sources](../../docker#build-openquake-docker-images)

***

## Getting help
If you need help or have questions/comments/feedback for us, you can:
  * Subscribe to the OpenQuake users mailing list: https://groups.google.com/forum/?fromgroups#!forum/openquake-users
  * Contact us on IRC: irc.freenode.net, channel #openquake

