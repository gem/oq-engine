(cluster)=

# Running on multiple nodes (cluster/zmq)

If you have a HPC cluster using the SLURM scheduler you are on the wrong
page and you should [go here](slurm.md) instead. This page documents how to
run the engine on a bare cluster of Linux machine without any scheduler.

The zmq workerpools run on the nodes as the tasks of a docker swarm
global service, one per node.

## Pre-requisites

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
communicate on the specified ports, and the nodes must be able to reach
each other on the ports used by docker swarm (2377/tcp for the managers,
7946/tcp and 7946/udp between the nodes).

### Storage requirements

Storage requirements depend a lot on the type of calculations you want
to run. On a worker node you will need just the space for the
operating system, the logs and the docker engine: less than 20GB are
usually enough.

On the master node you will also need space for:

- the `oqdata` folder of each user (usually `/home/<user>/oqdata`): it contains the calculations datastore (`hdf5` files)
- the OpenQuake database (located under `/opt/openquake/oqdata/`): it contains only logs and metadata, the expected size is tens of megabyte
- the temporary folder (`/tmp`). A different temporary folder can be customized via the `openquake.cfg`

On large installations we strongly suggest to create a separate partition for `/home`.

The workers read the engine code from the master, from a directory that
must be mounted at the same path on every node (see `swarm_code_dir`
below). They return their results to the master over ZMQ, while the
master writes the calculation datastore.

### Swap partitions

Having swap active on resources dedicated to the OpenQuake Engine is
_strongly discouraged_ because of the performance penality when it's
being used. It will likely increase by many orders of magnitude the
time required to complete the job, thus making the job actually stuck.
It is much better to get a MemoryError and then reduce the size of the job.

## Installation

### Master node

Please use the [Universal installation script](universal.md) in
`server` mode or `devel_server` mode. The installer will save the
Python code in the folder `/opt/openquake/venv`.

With `devel_server`, the engine code is the git clone of the repository,
which is the one the workers read. Clone it in `/opt/openquake/oq-engine`
and run `install.py devel_server` from there. Export `/opt/openquake` from
the master to the workers over NFS, and mount it at the same path on each
worker. To update the code, run `git pull` on the master: the workers see
the new code at once, but the workerpools must be restarted with
`oq workers start` to load it, when no calculation is running. The
repository should be owned by the `openquake` group, with write access
for the users who update it, so that `git pull` does not need root.

### Docker swarm

Install docker on every node, and create the swarm on the node that
will be the manager:

```
$ docker swarm init --advertise-addr <manager-ip>
```

To add a worker node, run on it the command printed by the previous
step, or get it again with `docker swarm join-token worker`. The master
must be a swarm manager, because it inspects the nodes to size the
memory limit of the workers. Check the nodes with `docker node ls`.

The workerpools run from an image that contains the dependencies of the
engine, but not its code, which is read from the master. Build it from
`docker/Dockerfile.workers`, from the root of the repository:

```
$ docker build -f docker/Dockerfile.workers -t <registry>/oq-workers:latest .
$ docker push <registry>/oq-workers:latest
```

The image must be rebuilt only when the dependencies in
`requirements-py312-linux64.txt` change.

The registry must be reachable from every node. If you have only one node,
the image can stay local.

## OpenQuake Engine 'master' node configuration File

The following file (on the master node) should be modified to enable
*zmq* support:

`/opt/openquake/venv/openquake.cfg`

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
# one entry for each node of the swarm: the IP address of the node,
# and the number of cores to use (-1 means all of them)
host_cores = < IP address of node1> -1, < IP address of node2> -1
ctrl_port = 1909
# the image of the workerpools, built as described above
swarm_image = <registry>/oq-workers:latest
# the engine code on the master, at the same path on every node
swarm_code_dir = /opt/openquake/oq-engine
# hard memory limit of each workerpool, in GB per core
memory_per_core = 2.5
```

Setting `swarm_image` turns on the swarm mode. The workerpools are then
the tasks of the docker swarm global service `oq-zworkerpool`, one on each
node, and `host_cores` must list all the nodes of the swarm: the engine does
not discover them by itself, so update it when a node is added or removed.
Without `swarm_image` the workerpools run only on the master machine, for
the entries of `host_cores` with address `127.0.0.1`.

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

There are a few useful commands to manage the workers, to be run on the
master:

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
