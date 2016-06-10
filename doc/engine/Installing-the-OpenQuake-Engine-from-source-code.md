# Running OpenQuake Engine from git repository on RedHat Linux and clones
This page describes the additional steps necessary to run the current development version of the OpenQuake engine rather than the latest public package using Ubuntu Linux 14.04 LTS or 12.04 LTS.

## Install primary dependencies
The easiest way to install the primary dependencies for OQ Engine is to install the latest stable Ubuntu package and then remove it, leaving in the place all of its dependencies.

Here's how:
```bash
sudo apt-get install software-properties-common
sudo add-apt-repository ppa:openquake-automatic-team/latest-master
sudo apt-get update
sudo apt-get install python-oq-engine
sudo apt-get remove --purge python-oq.*
```

## Install additional dependencies
A few additional packages are necessary if using GIT:
```bash
sudo apt-get install python-mock
```

## Get the source code from git
You'll now need to clone four source code package from git, including the OQ Engine itself. Change directory to someplace where you want to store the source code (somewhere in `/home/yourname` or `/usr/local/src/`, for example), then:
```
git clone https://github.com/gem/oq-engine.git
git clone https://github.com/gem/oq-hazardlib.git
git clone https://github.com/gem/oq-risklib.git
```

If you're planning on modifying your own copy of the code, you'll want to clone from your own fork instead.
See [forking a repository](https://help.github.com/articles/fork-a-repo).

## Set the PYTHONPATH and system PATH
You'll need to add to your `PYTHONPATH` environment variable the path to each source repo clone. In this example, we've cloned the repos (see above) to `/home/yourname/`. You can set your `PYTHONPATH` like so:
```bash
export PYTHONPATH=$HOME/oq-engine:$HOME/oq-hazardlib:$HOME/oq-risklib
export PATH=$HOME/oq-engine/bin:$PATH
```

To avoid having to do this in every session, it's a good idea to add this `export` statement to your `.profile`, located in your home directory.

## Bootstrap the database
Now you need to set up the OQ Engine database schema.

But first, we need to change a postgres configuration to allow this action. Edit your `/etc/postgresql/9.3/main/pg_hba.conf` file and add on top of the file these lines
```
local   openquake2   oq_admin                   md5
local   openquake2   oq_job_init                md5
```

You'll need to restart postgres for this change to take effect:
```sudo service postgresql restart```

Now set up the DB.
```bash
cd /path/to/oq-engine  # this is the source clone folder
sudo -u postgres ./bin/oq_create_db --db-name=openquake2
```

Finally upgrade the DB.

```bash
./bin/oq engine --upgrade-db
```

## Hazardlib speedups

To build the Hazardlib speedups see: https://github.com/gem/oq-hazardlib/wiki/Installing-C-extensions-from-git-repository

## Run OQ Engine
You are now ready to run the OQ Engine. First, try running one of the demos included with the source code:
```bash
./bin/oq engine --run=../oq-risklib/demos/hazard/SimpleFaultSourceClassicalPSHA/job.ini
```

The output should look something like this:
```
[2014-12-10 11:07:29,595 hazard job #114 - PROGRESS MainProcess/10696] **  executing (hazard)
[2014-12-10 11:07:29,620 hazard job #114 - PROGRESS MainProcess/10696] **  initializing sites
[2014-12-10 11:07:31,107 hazard job #114 - PROGRESS MainProcess/10696] **  initializing site collection
[2014-12-10 11:07:31,123 hazard job #114 - PROGRESS MainProcess/10696] **  initializing sources
[2014-12-10 11:07:31,562 hazard job #114 - PROGRESS MainProcess/10696] **  executing (hazard)
[2014-12-10 11:07:31,565 hazard job #114 - PROGRESS MainProcess/10696] **  Submitting task compute_hazard_curves #1
[2014-12-10 11:07:31,602 hazard job #114 - PROGRESS MainProcess/10696] **  Submitting task compute_hazard_curves #2
[2014-12-10 11:07:31,629 hazard job #114 - PROGRESS MainProcess/10696] **  Submitting task compute_hazard_curves #3
[2014-12-10 11:07:31,652 hazard job #114 - PROGRESS MainProcess/10696] **  Submitting task compute_hazard_curves #4
[2014-12-10 11:07:31,677 hazard job #114 - PROGRESS MainProcess/10696] **  Submitting task compute_hazard_curves #5
[2014-12-10 11:07:31,707 hazard job #114 - PROGRESS MainProcess/10696] **  Sent 0M of data
[2014-12-10 11:07:31,707 hazard job #114 - PROGRESS MainProcess/10696] **  spawned 5 tasks of kind compute_hazard_curves
[2014-12-10 11:07:43,501 hazard job #114 - PROGRESS MainProcess/10696] **  compute_hazard_curves  20%
[2014-12-10 11:07:48,412 hazard job #114 - PROGRESS MainProcess/10696] **  compute_hazard_curves  40%
[2014-12-10 11:07:57,615 hazard job #114 - PROGRESS MainProcess/10696] **  compute_hazard_curves  60%
[2014-12-10 11:08:01,970 hazard job #114 - PROGRESS MainProcess/10696] **  compute_hazard_curves  80%
[2014-12-10 11:08:02,480 hazard job #114 - PROGRESS MainProcess/10696] **  compute_hazard_curves 100%
[2014-12-10 11:08:02,596 hazard job #114 - PROGRESS MainProcess/10696] **  Received 10M of data
[2014-12-10 11:08:02,621 hazard job #114 - PROGRESS MainProcess/10696] **  post_executing (hazard)
[2014-12-10 11:08:02,621 hazard job #114 - PROGRESS MainProcess/10696] **  initializing realizations
[2014-12-10 11:08:10,177 hazard job #114 - PROGRESS MainProcess/10696] **  post_processing (hazard)
[2014-12-10 11:08:10,184 hazard job #114 - PROGRESS MainProcess/10696] **  Submitting task hazard_curves_to_hazard_map #1
[2014-12-10 11:08:10,195 hazard job #114 - PROGRESS MainProcess/10696] **  Submitting task hazard_curves_to_hazard_map #2
[2014-12-10 11:08:10,205 hazard job #114 - PROGRESS MainProcess/10696] **  Submitting task hazard_curves_to_hazard_map #3
[2014-12-10 11:08:10,215 hazard job #114 - PROGRESS MainProcess/10696] **  Submitting task hazard_curves_to_hazard_map #4
[2014-12-10 11:08:10,223 hazard job #114 - PROGRESS MainProcess/10696] **  Submitting task hazard_curves_to_hazard_map #5
[2014-12-10 11:08:10,233 hazard job #114 - PROGRESS MainProcess/10696] **  Submitting task hazard_curves_to_hazard_map #6
[2014-12-10 11:08:10,242 hazard job #114 - PROGRESS MainProcess/10696] **  Submitting task hazard_curves_to_hazard_map #7
[2014-12-10 11:08:10,252 hazard job #114 - PROGRESS MainProcess/10696] **  Submitting task hazard_curves_to_hazard_map #8
[2014-12-10 11:08:10,261 hazard job #114 - PROGRESS MainProcess/10696] **  Submitting task hazard_curves_to_hazard_map #9
[2014-12-10 11:08:10,272 hazard job #114 - PROGRESS MainProcess/10696] **  Sent 0M of data
[2014-12-10 11:08:10,272 hazard job #114 - PROGRESS MainProcess/10696] **  spawned 9 tasks of kind hazard_curves_to_hazard_map
[2014-12-10 11:08:10,814 hazard job #114 - PROGRESS MainProcess/10696] **  hazard_curves_to_hazard_map  11%
[2014-12-10 11:08:10,825 hazard job #114 - PROGRESS MainProcess/10696] **  hazard_curves_to_hazard_map  22%
[2014-12-10 11:08:10,861 hazard job #114 - PROGRESS MainProcess/10696] **  hazard_curves_to_hazard_map  33%
[2014-12-10 11:08:10,862 hazard job #114 - PROGRESS MainProcess/10696] **  hazard_curves_to_hazard_map  44%
[2014-12-10 11:08:10,875 hazard job #114 - PROGRESS MainProcess/10696] **  hazard_curves_to_hazard_map  55%
[2014-12-10 11:08:10,881 hazard job #114 - PROGRESS MainProcess/10696] **  hazard_curves_to_hazard_map  66%
[2014-12-10 11:08:10,885 hazard job #114 - PROGRESS MainProcess/10696] **  hazard_curves_to_hazard_map  77%
[2014-12-10 11:08:10,941 hazard job #114 - PROGRESS MainProcess/10696] **  hazard_curves_to_hazard_map  88%
[2014-12-10 11:08:11,383 hazard job #114 - PROGRESS MainProcess/10696] **  hazard_curves_to_hazard_map 100%
[2014-12-10 11:08:11,615 hazard job #114 - PROGRESS MainProcess/10696] **  Received 0M of data
[2014-12-10 11:08:13,469 hazard job #114 - PROGRESS MainProcess/10696] **  export (hazard)
[2014-12-10 11:08:13,527 hazard job #114 - PROGRESS MainProcess/10696] **  clean_up (hazard)
[2014-12-10 11:08:13,541 hazard job #114 - PROGRESS MainProcess/10696] **  complete (hazard)
Calculation 114 completed in 44 seconds. Results:
  id | output_type | name
1339 | Hazard Curve | Hazard Curve rlz-102-PGA
1340 | Hazard Curve | Hazard Curve rlz-102-PGV
1341 | Hazard Curve | Hazard Curve rlz-102-SA(0.025)
1342 | Hazard Curve | Hazard Curve rlz-102-SA(0.05)
1343 | Hazard Curve | Hazard Curve rlz-102-SA(0.1)
1344 | Hazard Curve | Hazard Curve rlz-102-SA(0.2)
1345 | Hazard Curve | Hazard Curve rlz-102-SA(0.5)
1346 | Hazard Curve | Hazard Curve rlz-102-SA(1.0)
1347 | Hazard Curve | Hazard Curve rlz-102-SA(2.0)
1338 | Hazard Curve (multiple imts) | hc-multi-imt-rlz-102
1352 | Hazard Map | Hazard Map(0.02) PGA rlz-102
1363 | Hazard Map | Hazard Map(0.02) PGV rlz-102
1357 | Hazard Map | Hazard Map(0.02) SA(0.025) rlz-102
1358 | Hazard Map | Hazard Map(0.02) SA(0.05) rlz-102
1356 | Hazard Map | Hazard Map(0.02) SA(0.1) rlz-102
1360 | Hazard Map | Hazard Map(0.02) SA(0.2) rlz-102
1359 | Hazard Map | Hazard Map(0.02) SA(0.5) rlz-102
1361 | Hazard Map | Hazard Map(0.02) SA(1.0) rlz-102
1365 | Hazard Map | Hazard Map(0.02) SA(2.0) rlz-102
1348 | Hazard Map | Hazard Map(0.1) PGA rlz-102
 ... | Hazard Map | 8 additional output(s)
1367 | Uniform Hazard Spectra | UHS (0.02) rlz-102
1366 | Uniform Hazard Spectra | UHS (0.1) rlz-102
Some outputs where not shown. You can see the full list with the command
`oq engine --list-outputs`
```

## More commands
For a list of additional commands, type `./bin/oq engine --help`.

## Getting help
If you need help or have questions/comments/feedback for us, you can:
  * Subscribe to the developer mailing list: https://groups.google.com/forum/?fromgroups#!forum/openquake-dev
  * Contact us on IRC: irc.freenode.net, channel #openquake
