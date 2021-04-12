# OpenQuake Kubernetes Deployments

## End user documentation

This page contain the first deployments of the engine for Kubernetes. These are experimental and not to use for production.
The right order of the yaml files:
engine-master-cfg.yaml: definition of map for configuration of openquake
svc-workers.yaml: definition of services for usings workers
svc-webui.yaml: definition of service for webui from master node
ingress-webui.yaml: definition of Ingress controller to have webui outside of cluster
deploy-master.yaml : deployment of one master from nightly docker image
deploy-worker.yaml:deployment of workers from nightly docker image

##

The main documentation, intended for end users on docker container, is available under the [documentation area](../doc/installing/docker.md)
##
