## Workaround
We are currently not supporting an installation of OpenQuake on Mac OS X, however we can recommend this workaround.

If you are running a Mac OS X (intel macs), we suggest that you use a virtual machine with an installation of Ubuntu to run OpenQuake.

* Download and install [VirtualBox 4.1.12](http://www.virtualbox.org/wiki/Downloads)
* Download and mount to VirtualBox an ISO of [Ubuntu 12.04](http://www.ubuntu.com/desktop/get-ubuntu/download)
* Continue with the [Ubuntu-12.04](https://github.com/gem/oq-engine/wiki/Ubuntu-12.04) installation instructions

## Installation from scratch
(tested with python 2.7 got from macports on Mac OSX Lion).

Install postgres 9.1 with python variant (`sudo port install postgresql91 +python`).
Install redis 2.0 from source (get it at redis.googlecode.com in the downloads section)
We assume that you have cloned both oq-engine and nrml. Install celery and rabbit from macports

`sudo port install rabbitmq-server py27-celery py27-psycopg2`

Make redis and rabbitmq launch at startup (`sudo port load rabbitmq-server` and `sudo port load redis`)

Assuming you have installed pip with the easy_install of macports (`easy_install pip`), then install
`pip install django redis h5py python-geohash guppy mock==0.7.2 launchpadlib postgis`

Install jpype:
`sudo env CPLUS_INCLUDE_PATH=/System/Library/Frameworks/JavaVM.framework/Versions/A/Headers pip install -e git://jpype.git.sourceforge.net/gitroot/jpype/jpype_05#egg=jpype`

Now you are able to start Celery by issuing `celeryd` from the oq-engine src directory.

Setup the the database (configure openquake.cfg for general setup and beware to use the psql from macports)
export PATH=/opt/local/lib/postgresql91/bin/:$PATH

at line 196 and 202 change the location of postgis properly to /opt/local/share/postgresql/9.1/contrib/postgis-1.5

gotcha: (create oq_ged4gem postgresql user)

Install java dependencies in /usr/share/java/, build oq java componets `ant build-openquake-jar`

Now you can execute openquake from the top source directory by issuing:
`PYTHONPATH=. ./bin/openquake --config_file demos/simple_fault_demo_hazard/config.gem --output_type=xml --log-level=debug`

Back to [Installation](https://github.com/gem/oq-engine/wiki/Installation)