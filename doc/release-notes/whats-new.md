Release notes (dev)
===================

```{note}
The DbServer is now a Django service, serving the internal `/v0` API on
the port `port` of the `[dbserver]` section of `openquake.cfg` (1908 by
default), while the WebUI serves the `/v1` API. The `[dbserver]` section
is the same as in version 3.26 and its `authkey` is the key required
by the DbServer.

- The DbServer runs only in `server` and `devel_server` installations,
  where it is managed by the systemd service `openquake-dbserver` and
  used by the regular users. The user `openquake` (i.e. the WebUI and
  the calculations started by it) and the `user` and `devel`
  installations access the database directly, whatever the `host`.
- In server installations only the DbServer upgrades the database, when
  it starts; the WebUI waits for it, so it must be started first. In
  `user` and `devel` installations this is done by `oq webui start`.
- In server installations the calculations left in the executing state
  are not marked as failed anymore when the WebUI starts, since that
  would also hit the calculations still running; use
  `oq db reset_is_running` when no calculation is running. In `user` and
  `devel` installations `oq webui start` still resets them.
- The WebUI service of a server installation runs with gunicorn, which
  is installed by `install.py`.
- In server installations `install.py` writes a random `authkey` in
  the `openquake.cfg` file it creates, instead of the default `changeme`.
- The development version of 3.27 renamed the section `[server]`: such
  configuration files must be changed back to `[dbserver]`, with the key
  `file` instead of `dbfile`, otherwise the engine raises an error.
```
