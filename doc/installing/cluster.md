# Running the OpenQuake Engine on multiple nodes (cluster configuration)

## Overall architecture
The nodes must all be able to communicate with the OpenQuake Engine *DbServer* and a *RabbitMQ* server.
Both services run on a single "master" node. It is not necessary and not recommended to run *RabbitMQ* on a worker node and *Celery* on master node.

Running OpenQuake on an *MPI cluster* is currently not supported. See the [FAQ](../faq.md#mpi-support) for more information.

## Initial install

Note: you have to **restart every celery node** after a configuration change.

### Ubuntu
On all nodes, install the `python-oq-engine` package as described in OpenQuake Engine installation for [Ubuntu](ubuntu.md).

### RedHat
For **RedHat** and derivates, install `python-oq-engine-master` package on the **master** node. It provides extra functionalities like _RabbitMQ_.
On the workers install `python-oq-engine-worker`; it adds _celery_ support on top of the standard `python-oq-engine` package.

## OpenQuake Engine 'master' node configuration File

### Enable Celery

In all the nodes, the following file should be modified to enable the *Celery* support:

`/etc/openquake/openquake.cfg:`

```
[distribution]
# enable celery only if you have a cluster
oq_distribute = celery
```

## OpenQuake Engine 'worker' node configuration File
On all worker nodes, the `/etc/openquake/openquake.cfg` file should be also modified to set the *DbServer* and *RabbitMQ* daemons IP address:

```
[amqp]
host = w.x.y.z
port = 5672
user = openquake
password = openquake
vhost = openquake
# This is where tasks will be enqueued.
celery_queue = celery

[dbserver]
# enable multi_user if you have a multiple user installation
multi_user = true
file = /var/lib/openquake/db.sqlite3
log = /var/lib/openquake/dbserver.log
host = w.x.y.z
port = 1908
authkey = changeme
```


### Configuring daemons

The required daemons are:

#### Master node
- RabbitMQ
- OpenQuake Engine DbServer
- OpenQuake Engine WebUI (optional)


##### RabbitMQ

A _user_ and _vhost_ are automatically added to the RabbitMQ configuration during the installation on `python-oq-engine`.

You can verify that the `openquake` user and vhost exist running:

```bash
# Check the user
sudo rabbitmqctl list_users | grep openquake 

# Check the vhost
sudo rabbitmqctl list_vhosts | grep openquake 
```

If, for any reason, the `openquake` user and vhost are missing they can be set up running:

```bash
# Add the user
sudo rabbitmqctl add_user openquake openquake

# Add the vhost
sudo rabbitmqctl add_vhost openquake
sudo rabbitmqctl set_permissions -p openquake openquake ".*" ".*" ".*"
```

For more information please refer to https://www.rabbitmq.com/man/rabbitmqctl.1.man.html.


#### Worker nodes
- Celery

*celery* must run all of the worker nodes. It can be started with

```bash
## RHEL
sudo service openquake-celery start
## Ubuntu
sudo supervisorctl start openquake-celery
```

The *Celery* daemon is not started at boot by default on the workers node and the *DbServer*, *WebUI* can be disabled on the workers. Have a look at the documentation for [Ubuntu](ubuntu.md#configure-the-system-services) or [RedHat](rhel.md#configure-the-system-services) to see how to enable or disable services.


### Monitoring Celery

The `celery-status` script is provided under `/usr/share/openquake/engine/utils` to check the status of the worker nodes, the task distribution and the cluster occupation. An output like this is produced:

```
==========
Host: celery@marley
Status: Online
Worker processes: 64
Active tasks: 0
==========
Host: celery@mercury
Status: Online
Worker processes: 64
Active tasks: 0
==========
Host: celery@dylan
Status: Online
Worker processes: 64
Active tasks: 0
==========
Host: celery@cobain
Status: Online
Worker processes: 64
Active tasks: 0
==========

Total workers:       256
Active tasks:        0
Cluster utilization: 0.00%
```


## Shared filesystem (optional)

OpenQuake 2.4 introduces the concept of _shared directory_ (aka _shared_dir_). This _shared dir_ allows the workers to read directly from the master's filesystem, thus increasing scalability and performance; this feature is optional: the old behaviour, transmitting data via `rabbitmq`, will be used when `shared_dir` isn't set.

The _shared directory_ must be exported from the master node to the workers via a _POSIX_ compliant filesystem (like **NFS**). The export may be (and _should_ be) exported and/or mounted as **read-only** by the workers.

As soon as the shared export is in place, the `shared_dir` config parameter in `openquake.cfg` must be configured to point to the path of the exported dir on the _master_ node and to where the export is mounted on each _worker_ node.

```
[directory]
# the base directory containing the <user>/oqdata directories;
# if set, it should be on a shared filesystem; for instance in our
# cluster it is /home/openquake; if not set, the oqdata directories
# go into $HOME/oqdata, unless the user sets his own OQ_DATADIR variable
shared_dir = /home/openquake
```

When `shared_dir` is set, the `oqdata` folders will be stored under `$shared_dir/<user>/oqdata` instead of `/home/<user>/oqdata`. See the comment in the `openquake.cfg` for further information.

You may need to give `RWX` permission to the `shared_dir` on _master_ to the `openquake` group (which is usually created by packages) and add all the cluster users to the `openquake` group. For example:

```bash
$ mkdir /home/openquake
$ chown openquake.openquake /home/openquake
# Enable setgid on the tree
$ chmod 2750 /home/openquake
```

On the workers the _shared_dir_ should be mounted as the `openquake` user too, or access must be given to the user running `celeryd` (which is `openquake` by default in the official packages).


## Network and security considerations

The worker nodes should be isolated from the external network using either a dedicated internal network or a firewall.
Additionally, access to the RabbitMQ, and DbServer ports should be limited (again by internal LAN or firewall) so that external traffic is excluded.

The following ports must be open on the **master node**:

* 5672 for RabbitMQ
* 1908 for DbServer
* 8800 for the API/WebUI (optional)

The **worker nodes** must be able to connect to the master on port 5672, and port 1908.


## Storage requirements

Storage requirements depend a lot on the type of calculations you want to run. On a worker node you will need just the space for the operating system, the logs and the OpenQuake installation: less than 20GB are usually enough. Workers can be also diskless (using iSCSI or NFS for example). Starting from OpenQuake 2.3 the software and all its libraries are located in `/opt/openquake`.

On the master node you will also need space for:
- the users' **home** directory (usually located under `/home`): it contains the calculations datastore (`hdf5` files located in the `oqdata` folder)
- the OpenQuake database (located under `/var/lib/openquake`): it contains only logs and metadata, the expected size is tens of megabyte
- *RabbitMQ* mnesia dir (usually located under `/var/lib/rabbitmq`)

On large installations we strongly suggest to create separate partition for `/home`, `/var` and *RabbitMQ* (`/var/lib/rabbitmq`).


## Swap partitions

Having swap active on resources dedicated to the OpenQuake Engine is _strongly discouraged_ because of the performance penality when it's being used and because how python allocates memory. In most cases (when memory throughput is relevant) is totally useless and it will just increase by many orders of magnitude the time required to complete the job (making the job actually stuck).


## Running calculations

Jobs can be submitted through the master node using the `oq engine` command line interface, the API or the WebUI if active. See the documentation about [how to run a calculation](../running/unix.md) or about how to use the [WebUI](../running/server.md)
