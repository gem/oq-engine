(cluster)=

# Running on multiple nodes (cluster/zmq)

If you have a HPC cluster using the SLURM scheduler you are on the wrong
page and you should [go here](slurm.md) instead. This page documents how to
run the engine on a bare cluster of Linux machine without any scheduler.

There are two ways to run the zmq workerpools on the nodes:

- **ssh mode**: the master starts and stops the workerpools on the
  workers via ssh, and the workers read the calculation files from a
  shared directory. This is the traditional setup, described first.
- **docker swarm mode**: the workerpools run as the tasks of a docker
  swarm global service, one per node. See [Docker swarm mode](#docker-swarm-mode)
  below.

## Pre-requisites

### Shared filesystem (ssh mode)

OpenQuake 2.4 introduced the concept of _shared directory_ (aka _shared_dir_). This _shared directory_ allows the workers to read directly from the master's filesystem, thus increasing scalability and performance; starting with OpenQuake 3.3 this feature is **mandatory** on a multi-node deployment.

The _shared directory_ must be exported from the master node to the workers via a _POSIX_ compliant filesystem (**NFSv4** is higly recommended). The export may be (and _should_ be) exported and/or mounted as **read-only** by the workers.

Starting from OpenQuake 2.3 the software and all its libraries are located in `/opt/openquake`. Also that folder must be exported from the master node to the workers.

As soon as the shared export is in place, the `shared_dir` config parameter in `openquake.cfg` must be configured to point to the path of the exported dir on the _master_ node and to where the export is mounted on each _worker_ node.

```
[directory]
# the base directory containing the <user>/oqdata directories:
# if set, it should be on a shared filesystem; this is **mandatory** on a multi-node cluster
# if not set, the oqdata directories go into $HOME/oqdata,
# unless the user sets his own OQ_DATADIR variable
shared_dir = /home
```
It is recommended to set as shared dir the `/home` folder: in such case `oqdata` will have the default path `/home/<user>/oqdata` and setgid is not required. Please note that the `openquake` user on workers still needs to get access to the `oqdata` content, so make sure that permission are properly set (`traverse` on the user home and `read` access to oqdata).

When `shared_dir` is set to a different value, the `oqdata` folders will be stored under `$shared_dir/<user>/oqdata` instead of `/home/<user>/oqdata`. See the comment in the `openquake.cfg` for further information.
You need then to give `RWX` permission to the `shared_dir` on _master_ to the `openquake` group (which is usually created by packages) and add all the cluster users to the `openquake` group. For example:

```bash
$ mkdir /oq_shared
$ chown openquake.openquake /oq_shared
# Enable setgid on the tree
$ chmod 2770 /oq_shared
```

On the workers the _shared_dir_ should be mounted as the `openquake` user too

```
[directory]
shared_dir = /oq_shared
```

It is not necessary to configure `openquake.cfg` for `/opt/openquake/venv`

The docker swarm mode does not use the shared directory: its service
mounts no host directory, and its workers run from the engine image.

### Network and security considerations

The worker nodes should be isolated from the external network using
either a dedicated internal network or a firewall. Also the WebUI
is meant to be used internally and should not face the public directly.

The following ports must be open on the **master node**:

* the `receiver_ports` range of the `[dbserver]` section of
  `openquake.cfg` (1912-1930 by default) for ZeroMQ receivers
* 8800 for the API/WebUI (optional)

The following port must be open on the **workers node**:

* 1909 for the ZeroMQ workerpools

The **master node** and the **worker nodes** must be able to
communicate on the specified ports.

In ssh mode, the user `openquake` on the master must be able to access the
workers via ssh. This means that you have to generate and copy the
ssh keys properly, and the first time you must connect to the workers
manually. Then the engine will be able to start and stop zworker
processes at each new calculation.

In docker swarm mode, the nodes must be able to reach each other on the
ports used by docker swarm (2377/tcp for the managers, 7946/tcp and
7946/udp between the nodes).

### Storage requirements

Storage requirements depend a lot on the type of calculations you want
to run. On a worker node you will need just the space for the
operating system, the logs and the OpenQuake installation: less than
20GB are usually enough. Workers can be also diskless (using iSCSI or
NFS for example).

On the master node you will also need space for:

- the **shared_dir** directory (usually located under `/home`): it contains the calculations datastore (`hdf5` files located in the `oqdata` folder)
- the OpenQuake database (located under `/opt/openquake/oqdata/`): it contains only logs and metadata, the expected size is tens of megabyte
- the temporary folder (`/tmp`). A different temporary folder can be customized via the `openquake.cfg`

On large installations we strongly suggest to create a separate partition for `/home`.

### Swap partitions

Having swap active on resources dedicated to the OpenQuake Engine is
_strongly discouraged_ because of the performance penality when it's
being used. It will likely increase by many orders of magnitude the
time required to complete the job, thus making the job actually stuck.
It is much better to get a MemoryError and then reduce the size of the job.

## Installation

### ssh mode

Please use the [Universal installation script](universal.md) in
`server` mode or `devel_server` mode. The installer will save the
Python code in the folder `/opt/openquake/venv`. Since
`/opt/openquake` is exported to the workers via NFS there will be no
need to install anything on the worker nodes except Python.

### Docker swarm mode

Install docker on every node, and create the swarm on the node that
will be the manager:

```
$ docker swarm init --advertise-addr <manager-ip>
```

To add a worker node, run on it the command printed by the previous
step, or get it again with `docker swarm join-token worker`. The master
must be a swarm manager, because it inspects the nodes to size the
memory limit of the workers. Check the nodes with `docker node ls`.

The workerpools run from an image that contains the engine. Build it from
`docker/Dockerfile.engine`, which installs from GitHub the branch given in
the `oq_branch` build argument, so that branch must be pushed first. From
the `docker` directory of the repository:

```
$ docker build -f Dockerfile.engine --build-arg oq_branch=<branch> \
    -t <registry>/oq-engine:latest .
$ docker push <registry>/oq-engine:latest
```

The registry must be reachable from every node. If you have only one node,
the image can stay local.

## OpenQuake Engine 'master' node configuration File

The following file (on the master node) should be modified to enable
*zmq* support:

`/opt/openquake/venv/openquake.cfg`

### ssh mode configuration

```
[distribution]
oq_distribute = zmq

[dbserver]
# address of the dbserver
# on multi-node cluster it must be the IP or hostname
# of the master node (on the master node cfg too)
host = < IP address of master>
receiver_ports = 1912-1930

[zworkers]
host_cores = < IP address of worker1> -1, < IP address of worker2> -1
ctrl_port = 1909
```

Notice that the -1 in `< IP address of worker1> -1` means that all the
cores in that worker will be used. You can use a number between 0 and
the maximum number of available core to limit the resource usage. The
engine will automatically start and stop zmq processes on the worker
nodes at each new calculation, *provided the user openquake has ssh
access to the workers*.  Please note that you must list explicitly the
workers that you want to use.

### Docker swarm mode configuration

```
[distribution]
oq_distribute = zmq

[dbserver]
host = < IP address of master>
receiver_ports = 1912-1930

[zworkers]
# one entry for each node of the swarm: the IP address of the node,
# and the number of cores to use (-1 means all of them)
host_cores = < IP address of node1> -1, < IP address of node2> -1
ctrl_port = 1909
# the image of the workerpools, built as described above
swarm_image = <registry>/oq-engine:latest
# hard memory limit of each workerpool, in GB per core
memory_per_core = 2.5
```

Setting `swarm_image` turns on the swarm mode. The workerpools are then
the tasks of the docker swarm global service `oq-zworkerpool`, one on each
node, and `host_cores` must list all the nodes of the swarm: the engine does
not discover them by itself, so update it when a node is added or removed.

Each workerpool container gets a hard memory limit of `memory_per_core` GB
for each core of the smallest node, so with 16-core nodes and the default
value each container can use 40 GB. The limit protects the host: if the
workers use more memory the container is killed, instead of the whole
machine running out of memory. The limit is set when the service is created;
to change it, remove the service with `docker service rm oq-zworkerpool` and
start the workerpools again.

### Common notes

NB: when using the zmq mechanism you should not touch the parameter
`serialize_jobs` and keep it at its default value of `true`.

### Configuring the WebUI service

The required systemd service is configured by the universal installer into the folder /etc/systemd/system/

#### Master node

- OpenQuake Engine WebUI - `openquake-webui.service`

### Monitoring zmq

`oq workers status` can be used to check the status of the worker nodes and the task distribution. An output like this is produced:

```
$ oq workers status
[('192.168.2.1', 1, 64), ('192.168.2.2', 7, 64), ('192.168.2.3', 7, 64)]
```
For each worker in the cluster you can see its IP and the cores which are
currently running with respect to the number of cores available (for instance
on the host 192.168.2.1 only 1 core of 64 is running, while in the other
two workers 7 cores are running each).

There are a few useful commands to manage the workers, to be run as user
`openquake`:

- `oq workers start` is used to start the workers
- `oq workers stop` is used to stop the workers nicely
- `oq workers kill` is used to send a hard `kill -9` to the workers
- `oq workers debug` is used to test that the installation is correct
- `oq workers wait` waits until all the workers are ready

In docker swarm mode, `oq workers start` on a service that already exists
restarts all its workerpools, so do not run it while a calculation is
running. `oq workers stop` leaves the service in place with no running
tasks, and `oq workers kill` force-restarts its tasks.

Adding a node to the swarm starts a workerpool on it automatically: add
the node to `host_cores` as well. To remove a node, drain it with
`docker node update --availability drain <node>`, which stops its
workerpool cleanly, and then remove it from `host_cores`.

If a calculation is stuck in the "executing" state due to an IT
problem (like the cluster running out of memory followed by an `oq
workers kill`) you can fix its status with the command `oq abort XXX`
where `XXX` is the calculation ID.

## Running calculations

Jobs can be submitted through the master node using the `oq engine` command line interface, the API or the WebUI if active. See the documentation about [how to run a calculation](../running-calculations/unix.rst) or about how to use the [WebUI](server.md)
