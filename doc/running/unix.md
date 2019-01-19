# Running the OpenQuake Engine

The OpenQuake Engine can be run via a command line interface or a WebUI. For the WebUI have a look to [its documentation](server.md).

## Running via command line interface (CLI)

The OpenQuake Engine command line tool is `oq`. To run a calculation the command `oq engine` must be run.

There are several demo calculations included with the package. Depending on the installation they are located in `/usr/share/openquake/engine/demos`. or `~/openquake/share/engine/demos/`or just `oq-engine/demos` in the source repository.

An example of running the `AreaSourceClassicalPSHA` demo:
```bash
[user@centos7 ~]$ oq engine --run /usr/share/openquake/engine/demos/hazard/AreaSourceClassicalPSHA/job.ini
```
The output should look something like this:

```
[2016-06-14 16:47:35,202 #2 INFO] Using engine version 2
[2016-06-14 16:47:35,333 #2 INFO] Read 528 hazard site(s)
[2016-06-14 16:47:35,386 #2 INFO] Parsed 1 sources from /usr/share/openquake/engine/demos/hazard/AreaSourceClassicalPSHA/source_model.xml
[2016-06-14 16:47:35,491 #2 INFO] Processed source model 1/1 with 1 gsim path(s)
[2016-06-14 16:47:35,546 #2 WARNING] Reducing the logic tree of source_model.xml from 1 to 0 realizations
[2016-06-14 16:47:35,597 #2 INFO] Instantiated SourceManager with maxweight=5.5
[2016-06-14 16:47:35,647 #2 INFO] Filtering light sources
[2016-06-14 16:47:35,694 #2 INFO] Filtering heavy sources
[2016-06-14 16:47:35,743 #2 INFO] splitting <AreaSource 1> of weight 41.0
[2016-06-14 16:47:35,856 #2 INFO] Submitting task classical #1
[2016-06-14 16:47:35,916 #2 INFO] Submitting task classical #2
[2016-06-14 16:47:35,966 #2 INFO] Submitting task classical #3
[2016-06-14 16:47:36,016 #2 INFO] Submitting task classical #4
[2016-06-14 16:47:36,076 #2 INFO] Submitting task classical #5
[2016-06-14 16:47:36,125 #2 INFO] Submitting task classical #6
[2016-06-14 16:47:36,179 #2 INFO] Submitting task classical #7
[2016-06-14 16:47:36,229 #2 INFO] Submitting task classical #8
[2016-06-14 16:47:36,284 #2 INFO] Sent 205 sources in 8 block(s)
[2016-06-14 16:47:36,360 #2 INFO] Sent 167.14 KB of data in 8 task(s)
[2016-06-14 16:47:43,515 #2 INFO] classical  12%
[2016-06-14 16:47:43,813 #2 INFO] classical  25%
[2016-06-14 16:47:44,170 #2 INFO] classical  37%
[2016-06-14 16:47:44,801 #2 INFO] classical  50%
[2016-06-14 16:47:49,680 #2 INFO] classical  62%
[2016-06-14 16:47:51,829 #2 INFO] classical  75%
[2016-06-14 16:47:51,949 #2 INFO] classical  87%
[2016-06-14 16:47:52,055 #2 INFO] classical 100%
[2016-06-14 16:47:52,110 #2 INFO] Received 6.67 MB of data, maximum per task 853.96 KB
[2016-06-14 16:47:59,660 #2 INFO] Calculation 2 finished correctly in 24 seconds
  id | name
   1 | hcurves
   2 | hmaps
   3 | uhs
```

To interrupt a running calculation simply press `CTRL-C`.

## More commands
For a list of additional commands, type `oq engine --help`.

## Running via SSH

When the OpenQuake Engine is driven via the `oq` command over an SSH connection an associated terminal must exist throughout the `oq` calculation lifecycle.

To avoid the `openquake.engine.engine.MasterKilled: The openquake master lost its controlling terminal` error you must make sure that a terminal is always associated with the `oq` process.

### Non-interactive use

For non-interactive jobs run in batch we suggest the use of `nohup` which is part of every Unix like OS:

```bash
[user@centos7 ~]$ nohup oq engine --run /usr/share/openquake/engine/demos/hazard/AreaSourceClassicalPSHA/job.ini &> /tmp/calc.log &
```

More info about `nohup`: [https://en.wikipedia.org/wiki/Nohup](https://en.wikipedia.org/wiki/Nohup).

### Interactive use

For an interactive use of `oq` we suggest to install [byobu](http://byobu.co/) on the target server and use it to run `oq`.

More info about `byobu`: [http://byobu.co/](http://byobu.co/).

## Getting help
If you need help or have questions/comments/feedback for us, you can:
  * Subscribe to the OpenQuake users mailing list: https://groups.google.com/forum/?fromgroups#!forum/openquake-users
  * Contact us on IRC: irc.freenode.net, channel #openquake
