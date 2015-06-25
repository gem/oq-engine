### Installing the OpenQuake Engine

Here's how to install the latest official engine package on Ubuntu 12.04:

If you want to keep your current OpenQuake 1.0 installation, or you need to install legacy software first remove the stable builds repository
<pre>
sudo add-apt-repository -r  ppa:openquake
</pre>

The following commands add the OpenQuake release 1.0 package repository
<pre>
sudo add-apt-repository ppa:openquake/release-1.0
sudo apt-get update
sudo apt-get install python-oq-.*
</pre>

### Upgrading the OpenQuake Engine to latest 1.0 release

The following command upgrades the OQ Engine and all its dependencies if an update is availble
```
sudo apt-get install python-oq-.*
```
Please remind that actually it will destroy your DB!

You have then to check the new configuration settings in ```/etc/openquake/openquake.cfg.new_in_this_release``` and merge them with your 
```/etc/openquake/openquake.cfg```. If you did not change the original ```openquake.cfg``` you can replace it with the new version
```bash
mv /etc/openquake/openquake.cfg.new_in_this_release /etc/openquake/openquake.cfg
```

**Please note**: PostgreSQL and RabbitMQ must be started, even on a worker node, to successful complete the upgrade. For example, the right upgrade procedure on a worker node is:
```
sudo service postgresql start
sudo service rabbitmq-server start
sudo apt-get install python-oq-.*
## Optional, stop the unused services on a worker node
sudo service postgresql stop
sudo service rabbitmq-server stop
```

## Run OQ Engine, without calculation parallelization
You are now ready to run the OQ Engine. First, try running one of the demos included with the package. There are several demo calculations located in `/usr/openquake/engine/demos`. Example:
<pre>
openquake --run-hazard=/usr/openquake/engine/demos/hazard/SimpleFaultSourceClassicalPSHA/job.ini --no-distribute
</pre>

The output should look something like this:
<pre>
[2013-05-31 11:13:32,979 hazard #1 1.0.0.127.in-addr.arpa PROGRESS MainProcess/33319 root] **  pre_executing (hazard)
[2013-05-31 11:13:33,753 hazard #1 1.0.0.127.in-addr.arpa PROGRESS MainProcess/33319 root] **  initializing sources
[2013-05-31 11:13:33,815 hazard #1 1.0.0.127.in-addr.arpa PROGRESS MainProcess/33319 root] **  initializing site model
[2013-05-31 11:13:34,166 hazard #1 1.0.0.127.in-addr.arpa PROGRESS MainProcess/33319 root] **  initializing realizations
[2013-05-31 11:13:34,352 hazard #1 1.0.0.127.in-addr.arpa PROGRESS MainProcess/33319 root] **  executing (hazard)
[2013-05-31 11:13:34,354 hazard #1 1.0.0.127.in-addr.arpa WARNING MainProcess/33319 root] Calculation task distribution is disabled
[2013-05-31 11:14:27,013 hazard #1 1.0.0.127.in-addr.arpa PROGRESS MainProcess/33319 root] **  > hazard 100% complete
[2013-05-31 11:14:27,364 hazard #1 1.0.0.127.in-addr.arpa PROGRESS MainProcess/33319 root] **  calculation 100% complete
[2013-05-31 11:14:27,372 hazard #1 1.0.0.127.in-addr.arpa PROGRESS MainProcess/33319 root] **  post_executing (hazard)
[2013-05-31 11:14:28,613 hazard #1 1.0.0.127.in-addr.arpa PROGRESS MainProcess/33319 root] **  post_processing (hazard)
[2013-05-31 11:14:28,615 hazard #1 1.0.0.127.in-addr.arpa PROGRESS MainProcess/33319 root] **  building arglist
[2013-05-31 11:14:28,619 hazard #1 1.0.0.127.in-addr.arpa PROGRESS MainProcess/33319 root] **  spawning 9 tasks of kind hazard_curves_to_hazard_map
[2013-05-31 11:14:29,965 hazard #1 1.0.0.127.in-addr.arpa PROGRESS MainProcess/33319 root] **  > hazard_curves_to_hazard_map 100% complete
[2013-05-31 11:14:30,246 hazard #1 1.0.0.127.in-addr.arpa PROGRESS MainProcess/33319 root] **  export (hazard)
[2013-05-31 11:14:30,261 hazard #1 1.0.0.127.in-addr.arpa PROGRESS MainProcess/33319 root] **  clean_up (hazard)
[2013-05-31 11:14:30,412 hazard #1 1.0.0.127.in-addr.arpa PROGRESS MainProcess/33319 root] **  complete (hazard)
Calculation 1 results:
id | output_type | name
8 | hazard_curve | hc-rlz-1
10 | hazard_curve | hc-rlz-1
2 | hazard_curve | hc-rlz-1
3 | hazard_curve | hc-rlz-1
4 | hazard_curve | hc-rlz-1
5 | hazard_curve | hc-rlz-1
6 | hazard_curve | hc-rlz-1
9 | hazard_curve | hc-rlz-1
7 | hazard_curve | hc-rlz-1
1 | hazard_curve_multi | hc-multi-imt-rlz-1
21 | hazard_map | hazard-map(0.1)-PGV-rlz-1
22 | hazard_map | hazard-map(0.02)-PGV-rlz-1
23 | hazard_map | hazard-map(0.1)-SA(0.025)-rlz-1
24 | hazard_map | hazard-map(0.02)-SA(0.025)-rlz-1
25 | hazard_map | hazard-map(0.1)-SA(0.2)-rlz-1
26 | hazard_map | hazard-map(0.02)-SA(0.2)-rlz-1
27 | hazard_map | hazard-map(0.1)-SA(1.0)-rlz-1
28 | hazard_map | hazard-map(0.02)-SA(1.0)-rlz-1
16 | hazard_map | hazard-map(0.02)-SA(2.0)-rlz-1
11 | hazard_map | hazard-map(0.1)-SA(0.05)-rlz-1
12 | hazard_map | hazard-map(0.02)-SA(0.05)-rlz-1
13 | hazard_map | hazard-map(0.1)-SA(0.5)-rlz-1
14 | hazard_map | hazard-map(0.02)-SA(0.5)-rlz-1
15 | hazard_map | hazard-map(0.1)-SA(2.0)-rlz-1
17 | hazard_map | hazard-map(0.1)-PGA-rlz-1
18 | hazard_map | hazard-map(0.02)-PGA-rlz-1
19 | hazard_map | hazard-map(0.1)-SA(0.1)-rlz-1
20 | hazard_map | hazard-map(0.02)-SA(0.1)-rlz-1
29 | uh_spectra | uhs-(0.1)-rlz-1
30 | uh_spectra | uhs-(0.02)-rlz-1
</pre>

## Run OQ Engine, with calculation parallelization
From the directory `/usr/openquake/engine`, launch celery worker processes like so:
<pre>
celeryd --purge &
</pre>

Then run `openquake` without the `--no-distribute` option:
<pre>
openquake --run-hazard=/usr/openquake/engine/demos/hazard/SimpleFaultSourceClassicalPSHA/job.ini
</pre>

## More commands
For a list of additional commands, type `openquake --help`.

## Getting help
If you need help or have questions/comments/feedback for us, you can:
  * Subscribe to the developer mailing list: https://groups.google.com/forum/?fromgroups#!forum/openquake-dev
  * Contact us on IRC: irc.freenode.net, channel #openquake