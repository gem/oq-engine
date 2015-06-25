### Server: ci2.openquake.org
### Jenkins configuration: [oq-engine-LRT](http://ci.openquake.org/job/oq-engine-LRT/)

***

To set up ci2.openquake.org to run long running tests, the following steps were taken to prepare the environment.

- Generate an SSH key as the `jenkins` user on ci.openquake.org and add it to the `authorized_keys` file for the `jenkins` user on ci2.openquake.org. This allows us to execute remote commands to ci2.openquake.org from the Jenkins context on ci.openquake.org without the need to authenticate.

- Follow the 'First time installation' [instructions for Ubuntu 11.10](https://github.com/gem/oq-engine/wiki/Ubuntu-11.10).

- Remove the package, since all we really want is to install the dependencies:

`sudo apt-get remove python-oq`

- Remove the config file created by the package. We don't want this to conflict with the latest openquake.cfg included in the source.

`sudo rm /etc/openquake/openquake.cfg`

- Install git and a few other dependencies for running oq-engine tests:

`sudo apt-get install git python-guppy python-mock python-nose openjdk-6-jdk ant libemma-java junit4 python-pip`

- Install `virtualenv` and `virtualenvwrapper`:

`sudo pip install virtualenv virtualenvwrapper`

Note: At the time of this document was created, ci2.openquake.org had the following virtualenv package versions installed (these were the latest available at the time). Different versions of these packages may warrant minor tweaks the build script in Jenkins.

`virtualenv==1.7.1.2`

`virtualenvwrapper==3.4`

- Clone the oq-engine repo to the current dir:

`git clone git://github.com/gem/oq-engine.git`

- CD into the source clone dir:

`cd oq-engine`

- Bootstrap the database (this creates tablespaces also):

`sudo -u postgres bin/create_oq_schema --db-name=openquake --schema-path=openquake/db/schema/`

- Add a role for jenkins to drop/build the db for running tests:

`sudo -u postgres psql -c "CREATE ROLE jenkins WITH SUPERUSER LOGIN;"`
`sudo -u postgres psql -c "ALTER ROLE jenkins WITH CREATEDB;"`

- Modify the postgres pg_hba.conf to enable trusted local authentication for the jenkins user:

`echo "local all jenkins trust" | sudo tee --append /etc/postgresql/9.1/main/pg_hba.conf`

- Restart postgres:

`sudo /etc/init.d/postgresql restart`

- Due to this [bug](https://bugs.launchpad.net/openquake/+bug/911714), apply this [patch](https://code.djangoproject.com/attachment/ticket/16778/postgis-adapter-2.patch).

- As `jenkins@ci2.openquake.org`:

`echo "export JAVA_HOME=/usr/lib/jvm/java-6-openjdk" >> $HOME/.bashrc`

- For logging celeryd output during the tests, we need to create a log file on ci2.openquake.org:

`sudo touch /tmp/celery.log`

`sudo chown jenkins /tmp/celery.log`

- I have also created a few scripts on ci2.openquake.org for starting and killing celery:

`/home/jenkins/start_celery.sh` [source...](https://raw.github.com/gist/2404416/29e84fc253f721dd6c9d77c018bc477edb37db74/start_celery.sh)

`/home/jenkins/kill_celery.sh` [source...](https://raw.github.com/gist/2404421/677d18e8d9436fb9ebdd88b1d1be0105ddc9394d/kill_celery.sh)

These scripts are called in various parts of the oq-engine-LRT jenkins config to run set up/tear down the test environment.

- To deploy the latest OpenSHA-lite jar into the LRT environment:

`sudo cp /usr/share/java/openshalite-1.2.jar /usr/share/java/openshalite-latest.jar`

Jenkins needs to own this file, so the oq-engine-LRT build config can refresh it:

`sudo chown jenkins /usr/share/java/openshalite-latest.jar`

Remove and recreate the symlink for /usr/share/java/openshalite.jar:

`sudo rm /usr/share/java/openshalite.jar`

`sudo ln -s /usr/share/java/openshalite-latest.jar /usr/share/java/openshalite.jar`

When the build runs, openshalite-latest.jar will be refreshed with the very latest build of OpenSHA-lite.