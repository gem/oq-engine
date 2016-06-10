# Installing the OpenQuake Engine nightly builds on Ubuntu Linux

Here's how to install the latest nightly engine package on **Ubuntu 12.04** and **Ubuntu 14.04**:

If you were previously using an official release first remove the old packages and the repository:
<pre>
sudo apt-get remove --purge python-oq.*
sudo add-apt-repository -r ppa:openquake/ppa
</pre>

The following commands add the nightly builds package repository
<pre>
sudo add-apt-repository ppa:openquake-automatic-team/latest-master
sudo apt-get update
sudo apt-get install python-oq-.*
</pre>

### Upgrading the OpenQuake Engine

The following command upgrades the OQ Engine and all its dependencies if an update is available
```
sudo apt-get install python-oq-.*
```

You have then to check the new configuration settings in ```/etc/openquake/openquake.cfg.new_in_this_release``` and merge them with your 
```/etc/openquake/openquake.cfg```. If you did not change the original ```openquake.cfg``` you can replace it with the new version
```bash
sudo mv /etc/openquake/openquake.cfg.new_in_this_release /etc/openquake/openquake.cfg
```

To compare cfg versions the ```diff``` utility is your friend:
```bash
sudo diff -urN /etc/openquake/openquake.cfg /etc/openquake/openquake.cfg.new_in_this_release
```
See an [example](openquake.cfg-diff-example.md).

## Run OQ Engine
You are now ready to run the OQ Engine. First, try running one of the demos included with the package. There are several demo calculations located in `/usr/share/openquake/engine/demos`. Example:
<pre>
oq-engine --run-hazard=/usr/share/openquake/engine/demos/hazard/SimpleFaultSourceClassicalPSHA/job.ini
</pre>

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
`oq-engine --list-outputs`
```

## More commands
For a list of additional commands, type `oq-engine --help`.

## Reset the database and drop the datastore
You can reset the OpenQuake Engine to start from a fresh installation:

```bash
oq_reset_db
```

This script will remove the database and the users datastore, then it will create a fresh new setup.

To run the script without interaction the flag `--yes` can be used. To just drop all the data without recreating the database the flag `--skip-new` can be used.

## Getting help
If you need help or have questions/comments/feedback for us, you can:
  * Subscribe to the developer mailing list: https://groups.google.com/forum/?fromgroups#!forum/openquake-dev
  * Contact us on IRC: irc.freenode.net, channel #openquake
