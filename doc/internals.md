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

Sometimes it's useful to run the DbServer in background for debug purposes. It can be started like this:

```bash
$ oq dbserver start
```

### Celery

Celery can be manually started via this command:

```bash
$ celery worker --config openquake.engine.celeryconfig --purge -Ofair
# if 'celery' is not in the system path 
$ python -m celery worker --config openquake.engine.celeryconfig --purge -Ofair
```
