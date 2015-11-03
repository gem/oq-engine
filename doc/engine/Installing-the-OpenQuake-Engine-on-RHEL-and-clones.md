This documentation explains how to install the OpenQuake Engine on RHEL 7 and its clones (CentOS, Scientific Linux) via EPEL. GEM provides preliminary support and binary RPMs for unstable (nightly builds) and stable releases. An experimental support for unstable releases is available also for Fedora 21/22/23.

## Dependencies

### Dependencies

The following dependencies are required. They will be installed automatically by the `oq-engine` package:

```
sudo python-amqp python-celery numpy scipy python-shapely python-psycopg2 python-django python-setuptools python-psutil python-mock python-futures rabbitmq-server postgresql-server postgis
```


### Install the OpenQuake Engine

Before installing the OpenQuake Engine you need to add [EPEL](https://fedoraproject.org/wiki/EPEL) and the _OpenQuake Packages_ [COPR](https://copr.fedoraproject.org/coprs/gem/openquake/) YUM repo:

#### Add EPEL repositories

```bash
$ sudo yum install https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm
```

#### Unstable releases and nightly builds

```bash
$ curl -s https://copr.fedoraproject.org/coprs/gem/openquake/repo/epel-7/gem-openquake-epel-7.repo | sudo tee /etc/yum.repos.d/gem-openquake-epel-7.repo
```

The full list of supported repos (including Fedora) is available on COPR: https://copr.fedoraproject.org/coprs/gem/openquake/

#### Stable releases (starting from OpenQuke Engine 1.5, EPEL only)


```bash
$ curl -s https://copr.fedoraproject.org/coprs/gem/openquake-stable/repo/epel-7/gem-openquake-stable-epel-7.repo | sudo tee /etc/yum.repos.d/gem-openquake-stable-epel-7.repo
```

Now it's possible to install the OpenQuake Engine using YUM:

```bash
$ sudo yum install python-oq-engine
```

### Post-installation tasks

## PostgreSQL initialization
```bash
$ sudo postgresql-setup initdb
```

Open `/var/lib/pgsql/data/pg_hba.conf` file and add on top of the file these lines
```
## localhost in IPv4
host   openquake2   oq_admin        127.0.0.1/32     md5
host   openquake2   oq_job_init     127.0.0.1/32     md5
## localhost in IPv6
host   openquake2   oq_admin        ::1/128       md5
host   openquake2   oq_job_init     ::1/128       md5
```
Then restart PostgreSQL
```bash
$ sudo service postgresql restart
```

## Start rabbitmq-server
```bash
$ sudo service rabbitmq-server start
```


## Bootstrap the DB
```bash
$ sudo -u postgres oq_create_db
$ oq-engine/bin/oq-engine --upgrade-db
```
A previously installed database can be removed running the `dropdb` tool
```bash
sudo -u postgres dropdb openquake2
```

## Start celery
```bash
$ cd /usr/share/openquake/engine && celery worker --purge -Ofair
```

## Run a demo
```bash
$ oq-engine --rh=/usr/share/openquake/risklib/demos/AreaSourceClassicalPSHA/job.ini
[2015-05-31 18:17:58,996 hazard job #407 - PROGRESS MainProcess/1562] **  pre_executing (hazard)
[2015-05-31 18:17:59,088 hazard job #407 - PROGRESS MainProcess/1562] **  initializing sites
[2015-05-31 18:17:59,660 hazard job #407 - PROGRESS MainProcess/1562] **  initializing site collection
[2015-05-31 18:17:59,679 hazard job #407 - PROGRESS MainProcess/1562] **  initializing sources
[2015-05-31 18:17:59,747 hazard job #407 - INFO MainProcess/1562] Processed <TrtModel #0 Active Shallow Crust, 205 source(s), 1640 rupture(s)>
[2015-05-31 18:17:59,779 hazard job #407 - INFO MainProcess/1562] Total weight of the sources=41.0
[2015-05-31 18:17:59,787 hazard job #407 - INFO MainProcess/1562] Expected output size=416064.0
[2015-05-31 18:17:59,812 hazard job #407 - PROGRESS MainProcess/1562] **  executing (hazard)
[2015-05-31 18:17:59,821 hazard job #407 - PROGRESS MainProcess/1562] **  Submitting task compute_hazard_curves #1
[...]
Calculation 407 completed in 50 seconds. Results:
  id | output_type | name
1485 | Hazard Curve | Hazard Curve rlz-356-PGA
1486 | Hazard Curve | Hazard Curve rlz-356-PGV
1487 | Hazard Curve | Hazard Curve rlz-356-SA(0.025)
1488 | Hazard Curve | Hazard Curve rlz-356-SA(0.05)
1489 | Hazard Curve | Hazard Curve rlz-356-SA(0.1)
1490 | Hazard Curve | Hazard Curve rlz-356-SA(0.2)
1491 | Hazard Curve | Hazard Curve rlz-356-SA(0.5)
1492 | Hazard Curve | Hazard Curve rlz-356-SA(1.0)
1493 | Hazard Curve | Hazard Curve rlz-356-SA(2.0)
1484 | Hazard Curve (multiple imts) | hc-multi-imt-rlz-356
1496 | Hazard Map | Hazard Map(0.02) PGA rlz-356
1497 | Hazard Map | Hazard Map(0.02) PGV rlz-356
1502 | Hazard Map | Hazard Map(0.02) SA(0.025) rlz-356
1499 | Hazard Map | Hazard Map(0.02) SA(0.05) rlz-356
1503 | Hazard Map | Hazard Map(0.02) SA(0.1) rlz-356
1507 | Hazard Map | Hazard Map(0.02) SA(0.2) rlz-356
1506 | Hazard Map | Hazard Map(0.02) SA(0.5) rlz-356
1509 | Hazard Map | Hazard Map(0.02) SA(1.0) rlz-356
1511 | Hazard Map | Hazard Map(0.02) SA(2.0) rlz-356
1494 | Hazard Map | Hazard Map(0.1) PGA rlz-356
 ... | Hazard Map | 8 additional output(s)
1513 | Uniform Hazard Spectra | UHS (0.02) rlz-356
1512 | Uniform Hazard Spectra | UHS (0.1) rlz-356
```
