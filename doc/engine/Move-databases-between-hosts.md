## On the source _"laptop"_

**Stop celery**
```bash
killall celeryd
```

#### Rename the OQ database
```bash
sudo -u postgres psql -c "ALTER DATABASE openquake RENAME TO openquake_laptop;"
```


#### Dump the renamed DB on /tmp
```bash
sudo -u postgres pg_dump -F d -f /tmp/openquake_laptop_dump openquake_laptop
sudo chown -R $(id -u).$(id -g) /tmp/openquake_laptop_dump
```


#### Transfer the dumped db folder
```bash
scp /tmp/openquake_laptop_dump [user@remote_ip]:
```


#### Revert the OQ database name to the default one
```bash
sudo -u postgres psql -c "ALTER DATABASE openquake_laptop RENAME TO openquake;"
```


## On the destination _"desktop"_

#### Make sure read permission are ok for the postgres user
```bash
chmod -R +r ~/openquake_laptop_dump
chmod +x ~/openquake_laptop_dump
```


#### Import the DB
```bash
sudo -u postgres pg_restore -d openquake -F d -C ~/openquake_laptop_dump/
```


#### Add permission for the migrated DB
in ```/etc/postgresql/9.1/main/pg_hba.conf```


**After**
```
local   openquake   oq_admin                   md5
local   openquake   oq_job_init                md5
```


**Add**
```patch
local   openquake_laptop   oq_admin                   md5
local   openquake_laptop   oq_job_init                md5
```


Restart PostgreSQL ```sudo service postgres restart``` 

#### Change the DB used by OpenQuake
**Stop celery**
```bash
killall celeryd
```


update the ```[database]``` section in ```/etc/openquake/openquake.cfg``` with the name of the new imported DB:

```patch
[database]
- name = openquake
+ name = openquake_laptop
host = localhost
port = 5432
```


**Start celery as usual**
```bash
cd /usr/openquake/engine; celeryd --purge &
```
