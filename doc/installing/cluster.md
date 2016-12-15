# Running the OpenQuake Engine on multiple nodes (cluster configuration)

## Overall architecture
The nodes must all be able to communicate with the OpenQuake Engine *DbServer* and a *RabbitMQ* server.
Both services run on a single "master" node. It is not necessary and not recommended to run *RabbitMQ* on a worker node and *Celery* on master node.

Running OpenQuake on an *MPI cluster* is currently not supported. See the [FAQ](../faq.md#mpi-support) for more information.

## Initial install
On all nodes, install the `python-oq-engine package` as described in OpenQuake Engine installation for [Ubuntu](ubuntu.md) or [RedHat](rhel.md).

Note: you have to **restart every celery node** after a configuration change.

## OpenQuake Engine 'master' node configuration File

### Enable Celery

In all the nodes, the following file should be modified to enable the *Celery* support:

`/etc/openquake/openquake.cfg:`

```
[celery]
# enable celery only if you have a cluster
use_celery = true
```

## OpenQuake Engine 'worker' node configuration File
On all worker nodes, the `/etc/openquake/openquake.cfg` file should be also modified to set the *DbServer* and *RabbitMQ* daemons IP address:

```
[amqp]
host = w.x.y.z
port = 5672
user = guest
password = guest
vhost = /
# This is where tasks will be enqueued.
celery_queue = celery

[dbserver]
# enable multi_user if you have a multiple user installation
multi_user = true
file = /var/lib/openquake/db.sqlite3
log = /var/lib/openquake/dbserver.log
host = w.x.y.z
port = 1999
authkey = changeme
```


### Configuring daemons

The required daemons are:

#### Master node
- RabbitMQ
- OpenQuake Engine DbServer
- OpenQuake Engine WebUI (optional)

#### Worker nodes
- Celery

*celery* must run all of the worker nodes. It can be started with

```bash
sudo service openquake-celery start
```

The *Celery* daemon is not started at boot by default on the workers node and the *DbServer*, *WebUI* can be disabled on the workers. Have a look at the documentation for [Ubuntu](ubuntu.md#configure-the-system-services) or [RedHat](rhel.md#configure-the-system-services) to see how to enable or disable services.


## Network and security considerations

The worker nodes should be isolated from the external network using either a dedicated internal network or a firewall.
Additionally, access to the RabbitMQ, and DbServer ports should be limited (again by internal LAN or firewall) so that external traffic is excluded.

The following ports must be open on the **master node**:

* 5672 for RabbitMQ
* 1999 for DbServer
* 8800 for the API/WebUI (optional)

The **worker nodes** must be able to connect to the master on port 5672, and port 1999.


## Storage requirements

Storage requirements depend a lot on the type of calculations you want to run. On a worker node you will need just the space for the operating system, the logs and the OpenQuake installation: less than 20GB are usually enough. Workers can be also diskless (using iSCSI or NFS for example).

On the master node you will also need space for:
- the users' **home** directory (usually located under `/home`): it contains the calculations datastore (`hdf5` files located in the `oqdata` folder)
- *RabbitMQ* mnesia dir (on RHEL usually located under `/var/lib/rabbitmq`)

On large installations we strongly suggest to create separate partition for `/home`, `/var` and *RabbitMQ* (`/var/lib/rabbitmq`).

## Running calculations

Jobs can be submitted through the master node using the `oq engine` command line interface, the API or the WebUI if active. See the documentation about [how to run a calculation](../running/unix.md) or about how to use the [WebUI](../running/server.md)
