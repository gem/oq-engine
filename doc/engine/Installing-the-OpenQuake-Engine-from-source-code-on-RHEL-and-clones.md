### Installing the OpenQuake Engine on RedHat Linux and clones
Supported releases: **RHEL / CentOS / SL 7** via EPEL.

## Dependencies

### RHEL/CentOS 7 only

Before installing the OpenQuake Engine you need to add [EPEL](https://fedoraproject.org/wiki/EPEL) and the _OpenQuake Packages_ [COPR](https://copr.fedoraproject.org/coprs/gem/openquake/    ) YUM repo:

#### Add EPEL and GEM repositories

```bash
$ sudo yum install https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm
```

```bash
$ curl -sL https://copr.fedoraproject.org/coprs/gem/openquake/repo/epel-7/gem-openquake-epel-7.repo | sudo tee /etc/yum.repos.d/gem-openquake-epel-7.repo

```
This provides some dependencies which are missing in **EPEL**.

### Install the OpenQuake Engine dependencies

```bash
$ sudo yum install sudo git gcc python-amqp python-celery numpy python-paramiko scipy python-shapely python-psycopg2 python-django python-setuptools python-psutil python-mock python-futures python-docutils rabbitmq-server postgresql-server h5py
```

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

## Get the OpenQuake Engine code
```bash
$ git clone https://github.com/gem/oq-engine.git
$ git clone https://github.com/gem/oq-hazardlib.git
$ git clone https://github.com/gem/oq-risklib.git
```
### Hazardlib speedups

To build the Hazardlib speedups see: https://github.com/gem/oq-hazardlib/wiki/Installing-C-extensions-from-git-repository

## Set the PYTHONPATH and system PATH
You'll need to add to your `PYTHONPATH` environment variable the path to each source repo clone. In this example, we've cloned the repos (see above) to `/home/yourname/`. You can set your `PYTHONPATH` and  `PATH` like so:
```bash
export PYTHONPATH=$HOME/oq-engine:$HOME/oq-hazardlib:$HOME/oq-risklib
export PATH=$HOME/oq-engine/bin:$PATH
```

## Configure the Engine and bootstrap the DB
```bash
$ sudo -u postgres oq-engine/bin/oq_create_db
$ oq-engine/bin/oq engine --upgrade-db
```

