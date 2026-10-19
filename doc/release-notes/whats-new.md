Release notes (dev)
===================

```{warning}
The `[dbserver]` section of `openquake.cfg` does not exist anymore.
Starting from version 3.27 its keys live in the `[server]` section:

- `host`, `receiver_host` and `receiver_ports` keep their names;
- `file` has been renamed `dbfile`;
- the `port` key has been removed;
- the `oq dbserver` command and the DbServer daemon have been removed.

Versions up to 3.26, including the LTS release 3.23, still use the
`[dbserver]` section with the `file` key, so the configuration files
must be updated when upgrading.
```
