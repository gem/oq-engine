# Internal commands

This commands and internals are meant to be used for debug and development. They MAY CHANGE ANYTIME, without notice.

### Database creation

The database is automatically created when running a calculation, but it can also be manually created via

```bash
$ python -m openquake.server.db.upgrade_manager ~/oqdata/db.sqlite3
```

### Database commands

- `oq db get_executing_jobs`
- `oq db get_longest_jobs`
- `oq db find <description>`

### Django management and migrations

The OpenQuake server uses Django for the web/API application. Management can be done via:

```bash
$ oq webui [help]
```
The `oq webui` command provides a limited subset of commands. To be able to access all the available commands in Django the following command must be used.

```bash
$ python -m openquake.server.manage [help]
```

Using packages, when a custom local_settings.py is used, the command must be run from `/usr/share/openquake/engine`.

```bash
$ cd /usr/share/openquake/engine
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

A custom port can be also specified via `OQ_DBSERVER_PORT` env variable:

```bash
$ OQ_DBSERVER_PORT=1985 oq dbserver start
```

### Celery

Celery can be manually started via this command:

```bash
$ celery worker --config openquake.engine.celeryconfig --purge -Ofair
# if 'celery' is not in the system path 
$ python -m celery worker --config openquake.engine.celeryconfig --purge -Ofair
```
