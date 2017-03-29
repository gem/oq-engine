# Internal commands

This commands and internals are meant to be used for debug and development. DO NOT USE them in production. They MAY CHANGE ANYTIME, without notice.

### Database creation

Database is created by `oq` itself, it can be manually created via

```bash
$ python -m openquake.server.db.upgrade_manager ~/oqdata/db.sqlite3
```

### Django management and migrations

The OpenQuake server uses Django for the web/API application. Management can be done via:

```bash
$ python -m openquake.server.manage [help]
```

### DbServer

Sometimes it's useful to run the DbServer in foreground for debug purposes. It can be started like this:

```bash
$ oq dbserver start
```

A custom binging address and port can be specified at startup time as a custom db path too:

```bash
$ oq dbserver start 0.0.0.0:1985 /tmp/customdb.sqlite3
```

### Celery

Celery can be manually started via this command:

```bash
$ celery worker --config openquake.engine.celeryconfig --purge -Ofair
# if 'celery' is not in the system path 
$ python -m celery worker --config openquake.engine.celeryconfig --purge -Ofair
```
