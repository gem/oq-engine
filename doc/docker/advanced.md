# Docker advanced options

## Authentication support

Authentication support for the WebUI/API can be enabled passing the `LOCKDOWN` environment variable to the Docker container:

```bash
$ docker run -e LOCKDOWN=enabled --name myoqcontainer -d -p 8800:8800 openquake/engine:nightly "oq webui start"
```

### Docker

- [Introduction](../installing/docker.md)
- [Single node deployment](single.md)

## Getting help
If you need help or have questions/comments/feedback for us, you can subscribe to the OpenQuake users mailing list: https://groups.google.com/g/openquake-users

