## Initial install
On all nodes, install Ubuntu and the python-oq package as described in [OpenQuake Engine installation](Installing-the-OpenQuake-Engine.md) or [OpenQuake Engine Master installation](Installing-the-OpenQuake-Engine-Nightly.md).

## Overall architecture 
The nodes must all be able to communicate with a single Redis Key-Value store (only for OpenQuake <= 1.0), a single PostresSQL database and a single RabbitMQ server.
One common configuration is to install and deploy all three services on a single "control node" server, but other configurations are possible.  It is not necessary and not normally recommended to install redis, postres or RabbitMQ on the worker nodes.

## Postgres configuration
The default Postgres configuration does not permit access from other machines: the file /etc/postgresql/9.3/main/pg_hba.conf should be modified to allow access to the "openquake" database from the worker nodes, an example excerpt follows:

### OpenQuake 1.0
<pre>
host   openquake   oq_admin        192.168.10.0/8 md5
host   openquake   oq_job_init     192.168.10.0/8 md5
host   openquake   oq_job_superv   192.168.10.0/8 md5
host   openquake   oq_reslt_writer 192.168.10.0/8 md5
</pre>

### OpenQuake >= 1.2
<pre>
host   openquake2   oq_admin        192.168.10.0/8 md5
host   openquake2   oq_job_init     192.168.10.0/8 md5
</pre>

The Postgres manual describes a number of runtime configuration parameters that may need to be adjusted depending on your cluster configuration:

### listen_addresses 
* See [http://www.postgresql.org/docs/current/static/runtime-config-connection.html#GUC-LISTEN-ADDRESSES](http://www.postgresql.org/docs/current/static/runtime-config-connection.html#GUC-LISTEN-ADDRESSES)

By default Postres, on Ubuntu, allows connections only from localhost. Since celery workers need to push data back to Postgres, it should be exposed to the cluster network:

/etc/postgresql/9.3/main/postgresql.conf
<pre>
# This value should be at least the number of worker cores
listen_addresses = '*'
</pre>

### max_connections 
* See [http://www.postgresql.org/docs/current/static/runtime-config-connection.html#GUC-MAX-CONNECTIONS](http://www.postgresql.org/docs/current/static/runtime-config-connection.html#GUC-MAX-CONNECTIONS)

By default Postres allows a maximum of 100 simultaneous connections. By default celery will create a worker process for each available core and the OpenQuake Engine uses two connection per worker, so max_connections should be at least twice number of available worker cores (2 * CPU in the cluster).

Note that changing max_connections may also imply operating-system level changes, please see [http://www.postgresql.org/docs/current/static/kernel-resources.html](http://www.postgresql.org/docs/current/static/kernel-resources.html) for details.

/etc/postgresql/9.3/main/postgresql.conf
<pre>
# This value should be at least the number of worker cores
max_connections = 100
</pre>

Note: you have to **restart every celery node** after a PostgreSQL configuration change or a restart.

## Redis configuration (only for OpenQuake <= 1.0)
By default, Redis does not permit access from other machines. The "bind" parameter in the /etc/redis/redis.conf file should be either:
  * set to the IP Address of the interface on which to accept incoming connections.  
  * commented or not preset so that Redis listens for connections on all interfaces

The /etc/redis/redis.conf file should also be edited to set the timeout parameter to 0.  (See [https://bugs.launchpad.net/openquake/+bug/907760](https://bugs.launchpad.net/openquake/+bug/907760) for details).
<pre>
timeout=0
</pre>

See also security considerations below.

## OpenQuake engine Master node Configuration File
In the master node, the following file should be modified to refer to the Postres, Redis and Rabbit servers:

/etc/openquake/openquake.cfg:

```
terminate_job_when_celery_is_down = false
# this is good generally, but it may be necessary to turn it off in
# heavy computations (i.e. celery could not respond to pings and still
# not be really down).

```

```
# maximum number of tasks to spawn concurrently
concurrent_tasks = [number_of_workers * 2]
```

The ```concurrent_tasks``` value must be set at _[number_of_workers * 2]_ (on a 128 cores cluster it would be 256).

**NOTE** that the /etc/openquake/openquake.cfg file can be overridden by an openquake.cfg file in the current working directory.

## OpenQuake engine Worker node Configuration File
On all worker nodes, the following file should be modified to refer to the Postres, Redis and Rabbit servers:

```/etc/openquake/openquake.cfg``` (see the ```/etc/openquake/openquake_workers.cfg``` as reference):
```
### Only for OQE <= 1.0.0
[kvs]
port = 6379
## replace localhost with hostname for Redis KVS
host = localhost
### End OQE <= 1.0.0 only

[amqp]
# Replace localhost with hostname for RabbitMQ
host = localhost
port = 5672

# See the RabbitMQ "Access Control" page for details of the vhost parameter
# http://www.rabbitmq.com/access-control.html
vhost = /

[database]
name = openquake
# replace localhost with the hostname for the Postgres DB
host = localhost
port = 5432
```

## Running calculations

Jobs can be submitted through the master node using the `oq-engine` command line interface.

`celeryd` must run all of the worker nodes. We strongly suggest to use `supervisord` to manage the celery deamons.

```supervisord``` can be installed with
```bash
sudo apt-get install supervisor
```

An example of configuration for the OpenQuake Engine is
```
openquake@node01:~$ sudo cat /etc/supervisor/conf.d/celeryd.conf 
[program:celery]
command=celeryd --purge
directory=/usr/local/openquake/oq-engine
user=celery
group=celery
#numprocs=1
stdout_logfile=/var/log/celery/openquake.log
stderr_logfile=/var/log/celery/openquake.log
autostart=false
autorestart=true
startsecs=10

; Need to wait for currently executing tasks to finish at shutdown.
; Increase this if you have very long running tasks.
stopwaitsecs = 600

; When resorting to send SIGKILL to the program to terminate it
; send SIGKILL to its whole process group instead,
; taking care of its children as well.
killasgroup=true
```

A custom `PYTHONPATH` can be also set
```
environment=PYTHONPATH="/usr/local/openquake/oq-engine:/usr/local/openquake/oq-hazardlib:/usr/local/openquake/oq-nrmllib:/usr/local/openquake/oq-risklib",DJANGO_SETTINGS_MODULE="openquake.engine.settings",OQ_LOCAL_CFG_PATH="openquake_worker.cfg" 
```



## Network and security considerations
The worker nodes should be isolated from the external network using either a dedicated internal network or a firewall.
Additionally, access to the redis, rabbit, and postgres ports should be limited (again by internal LAN or firewall) so that external traffic is excluded.

It is not recommended to run the Celery daemon as root.
If using `supervisord` (or similar) to execute `celeryd` at boot time please ensure that celery is not run as the _root_ user.

## Storage requirements

Storage requirements depend a lot on the type of calculations run. On a worker node you will need just the space for the operating system, the logs and the OpenQuake installation: less than 20GB are usually enough. Workers can be also diskless (using iSCSI or NFS for example).

On the master node you will also need space for the PostgreSQL DB and for the RabbitMQ mnesia dir. Both are located in ```/var```, but on large installation we strongly suggest to create separate partition for ```/var```, PostgreSQL (```/var/lib/postgres```) and RabbitMQ (```/var/lib/rabbitmq```).
Those partitions should be stored on fast local disks or on a high performance SAN (i.e. using a FC or a 10Gbps link).
