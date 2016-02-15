### Supported operating systems

#### Ubuntu 
[Ubuntu 12.04 LTS](Installing-the-OpenQuake-Engine.md) and [Ubuntu 14.04 LTS](Installing-the-OpenQuake-Engine.md), both 32 and 64 bit, are supported and deb packages provided.

#### RHEL / CentOS / SL

[RHEL7 and its clones](Installing-the-OpenQuake-Engine-on-RHEL-and-clones.md) are supported and RPM packages provided.

***

### Celery support

Starting from release 1.8 Celery isn't needed (and not recommended) on a single machine setup anymore; the OpenQuake Engine is able to use all the available CPU cores even without Celery.
Celery can still be enabled on a cluster / multi node setup. To enable it please refer to the multiple nodes installation guidelines for [Ubuntu](Running-the-OpenQuake-Engine-on-multiple-RHEL-nodes.md)
or [RHEL](Running-the-OpenQuake-Engine-on-multiple-RHEL-nodes.md).

***

### DatabaseError: invalid byte sequence for encoding "UTF8": 0x00 (Ubuntu 12.04 only)

A more detailed stack trace:

```Python
Traceback (most recent call last):
  File "/usr/bin/openquake", line 9, in <module>
    load_entry_point('openquake==0.8.3', 'console_scripts', 'openquake')()
  File "/usr/lib/pymodules/python2.7/openquake/bin/oqscript.py", line 192, in main
    args.config_file, ajob, user_name, args.force_inputs)
  File "/usr/lib/pymodules/python2.7/openquake/engine.py", line 996, in import_job_profile
    job_profile = _prepare_job(params, sections, user_name, job, force_inputs)
  File "/usr/lib/python2.7/dist-packages/django/db/transaction.py", line 217, in inner
    res = func(*args, **kwargs)
  File "/usr/lib/pymodules/python2.7/openquake/engine.py", line 718, in _prepare_job
    job_profile = _get_job_profile(calc_mode, job_type, owner)
  File "/usr/lib/python2.7/dist-packages/django/db/transaction.py", line 217, in inner
    res = func(*args, **kwargs)
  File "/usr/lib/pymodules/python2.7/openquake/engine.py", line 706, in _get_job_profile
    job_profile.save()
  File "/usr/lib/python2.7/dist-packages/django/db/models/base.py", line 460, in save
    self.save_base(using=using, force_insert=force_insert, force_update=force_update)
  File "/usr/lib/python2.7/dist-packages/django/db/models/base.py", line 553, in save_base
    result = manager._insert(values, return_id=update_pk, using=using)
  File "/usr/lib/python2.7/dist-packages/django/db/models/manager.py", line 195, in _insert
    return insert_query(self.model, values, **kwargs)
  File "/usr/lib/python2.7/dist-packages/django/db/models/query.py", line 1436, in insert_query
    return query.get_compiler(using=using).execute_sql(return_id)
  File "/usr/lib/python2.7/dist-packages/django/db/models/sql/compiler.py", line 791, in execute_sql
    cursor = super(SQLInsertCompiler, self).execute_sql(None)
  File "/usr/lib/python2.7/dist-packages/django/db/models/sql/compiler.py", line 735, in execute_sql
    cursor.execute(sql, params)
  File "/usr/lib/python2.7/dist-packages/django/db/backends/postgresql_psycopg2/base.py", line 44, in execute
    return self.cursor.execute(query, args)
django.db.utils.DatabaseError: invalid byte sequence for encoding "UTF8": 0x00
```

This error is related to a bug in Django 1.3.x and requires a custom PostgreSQL configuration. To fix it edit the ```/etc/postgresql/9.1/main/postgresql.conf``` file and set ```standard_conforming_strings``` to **off**:

```standard_conforming_strings = off```

Save and restart PostgreSQL

```bash 
$ sudo service postgresql restart
```

See also:
* [https://bugs.launchpad.net/openquake/+bug/911714](https://bugs.launchpad.net/openquake/+bug/911714)
* [https://code.djangoproject.com/ticket/16778](https://code.djangoproject.com/ticket/16778)

***

### ConnectionError: Error 111 connecting localhost:6379. Connection refused.

A more detailed stack trace:

```Python
File "/usr/lib/pymodules/python2.6/redis/client.py", line 315, in _execute_command
    self.connection.send(command, self)
File "/usr/lib/pymodules/python2.6/redis/client.py", line 82, in send
    self.connect(redis_instance)
File "/usr/lib/pymodules/python2.6/redis/client.py", line 62, in connect
    raise ConnectionError(error_message)
redis.exceptions.ConnectionError: Error 111 connecting localhost:6379. Connection refused.
```

This is because Redis server is not running. You can start it running
```bash
$ sudo service redis-server start
```

***
### error: [Errno 111] Connection refused

A more detailed stack trace:

```Python
File "/usr/local/lib/python2.6/dist-packages/carrot/connection.py", line 135, in connection
    self._connection = self._establish_connection()
File "/usr/local/lib/python2.6/dist-packages/carrot/connection.py", line 148, in _establish_connection
    return self.create_backend().establish_connection()
File "/usr/local/lib/python2.6/dist-packages/carrot/backends/pyamqplib.py", line 208, in establish_connection
    connect_timeout=conninfo.connect_timeout)
File "/usr/local/lib/python2.6/dist-packages/amqplib/client_0_8/connection.py", line 125, in __init__
    self.transport = create_transport(host, connect_timeout, ssl)
File "/usr/local/lib/python2.6/dist-packages/amqplib/client_0_8/transport.py", line 220, in create_transport
    return TCPTransport(host, connect_timeout)
File "/usr/local/lib/python2.6/dist-packages/amqplib/client_0_8/transport.py", line 58, in __init__
    self.sock.connect((host, port))
File "", line 1, in connect
error: [Errno 111] Connection refused
```

This is because RabbitMQ server is not running. You can start it running
```bash
$ sudo service rabbitmq-server start
``` 

***
### RabbitMQ log file grows too fast

This happens because RabbitMQ default log level is **INFO** and every connection is logged.
To avoid this, if you are using RabbitMQ >= 2.8 (provided by the OpenQuake > 1.0), simply create the file ```/etc/rabbitmq/rabbitmq.config``` with this content

```erlang
[
   {rabbit, [{log_levels, [{connection, warning}]}]}
].
```
and restart RabbitMQ

```bash
$ sudo service rabbitmq-server restart
```
