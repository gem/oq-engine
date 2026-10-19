.. _zmq-cluster:

Setting up a zmq cluster with docker swarm
==========================================

The engine can distribute the work of a calculation over several nodes
using the ``zmq`` mode: each node runs one *workerpool*, a process that
starts a pool of workers and listens for tasks on a ZMQ control port
(by default 1909). The master, i.e. the machine where you run the
calculation, sends the tasks to the workerpools. This page explains how
to run the workerpools as the tasks of a `docker swarm
<https://docs.docker.com/engine/swarm/>`_ global service, which starts one
workerpool on every node of the swarm.

Requirements
------------

* Docker installed on every node, and the nodes must be able to reach
  each other on the network.
* The master must be a swarm manager, because it inspects the nodes to
  size the memory limit of the workers.
* The master must be able to reach the control port (TCP 1909 by default)
  of every node, because the workerpools are published on the host.
* An image of the engine that the nodes can pull, see below.

Step 1: create the swarm
------------------------

On the node that will be the manager, run::

  $ docker swarm init --advertise-addr <manager-ip>

To add a worker node, run the command printed by the previous step on
that node, or get it again with::

  $ docker swarm join-token worker

Check the result on the manager with ``docker node ls``.

Step 2: build and publish the image
-----------------------------------

The workerpools run from an image that contains the engine. The image is
built from ``docker/Dockerfile.engine``, which installs the branch given
in the ``oq_branch`` build argument from GitHub, so that branch must be
pushed first and must contain the swarm support. From the ``docker``
directory of the repository::

  $ docker build -f Dockerfile.engine --build-arg oq_branch=master \
      -t <registry>/oq-engine:latest .
  $ docker push <registry>/oq-engine:latest

``<registry>`` must be a registry that every node can pull from. If you
have only one node, the image can also stay local.

Step 3: configure the master
----------------------------

In the ``openquake.cfg`` file used by the master, set the distribution
mode and the swarm settings in the ``[distribution]`` and ``[zworkers]``
sections::

  [distribution]
  oq_distribute = zmq

  [zworkers]
  # one entry "host cores" for each node of the swarm: the host is the
  # address of the node, cores is the number of cores to use (-1: all)
  host_cores = 192.168.9.2 -1,192.168.9.3 -1
  ctrl_port = 1909
  # the image of the workerpools, from step 2
  swarm_image = <registry>/oq-engine:latest
  # hard memory limit of each workerpool, in GB per core (the default)
  memory_per_core = 2.5

Setting ``swarm_image`` turns on the swarm mode: the workerpools are the
tasks of the swarm global service ``oq-zworkerpool``, one per node. In
this mode ``host_cores`` still lists the nodes, and it must list all of
them: the engine does not discover the nodes of the swarm by itself.

Step 4: start the workerpools
-----------------------------

On the master, run::

  $ oq workers start

The first time, this creates the service ``oq-zworkerpool``. The service
runs one task on each node and publishes the control port on it. Check
that the workerpools are running with::

  $ oq workers status

which prints a list with one entry for each running workerpool, giving
its address, the number of executing tasks and the number of workers,
for example ``[('192.168.9.2:1909', 0, 16)]``. Use ``oq workers wait`` to
wait until all the workerpools are ready.

Memory limit
------------

Each workerpool container gets a hard memory limit of ``memory_per_core``
GB for each core of the smallest node of the swarm, so with 16-core nodes
and the default value each container can use 40 GB. The limit protects the
host: if the workers use more memory, the container is killed instead of
the whole machine running out of memory. The limit is set when the service
is created. To change it, remove the service and start it again::

  $ docker service rm oq-zworkerpool
  $ oq workers start

Adding and removing nodes
-------------------------

To add a node, join it to the swarm (step 1). The swarm then starts a
workerpool on it automatically. Add the node to ``host_cores`` on the
master, so that the engine sends it tasks: the list must match the nodes
of the swarm.

To remove a node, drain it first, so that its workerpool stops cleanly
(it exits on ``SIGTERM``, as with ``oq workers stop``)::

  $ docker node update --availability drain <node>

Then remove the node from ``host_cores`` and, if it should leave the
swarm, run ``docker swarm leave`` on that node. To use it again, set its
availability back with ``docker node update --availability active <node>``.

Note that ``oq workers start`` on an existing service restarts all its
workerpools, so do not run it while a calculation is running. Use
``oq workers status`` to check the workerpools first.

Stopping and killing
--------------------

``oq workers stop`` asks all the workerpools to stop. A stopped workerpool
exits and the swarm does not restart it, so the service stays in place
with no running tasks until the next ``oq workers start``.

``oq workers kill`` force-restarts the tasks of the service, which kills
the workers of all the nodes, for example after a hard out-of-memory
situation.

Troubleshooting
---------------

* A node is missing from ``oq workers status``: check that its port 1909
  is open and that its workerpool task is running with
  ``docker service ps oq-zworkerpool``.
* The service logs are available with ``docker service logs
  oq-zworkerpool``.
* If the master fails to inspect the nodes, check that it is a swarm
  manager with ``docker node ls``.
