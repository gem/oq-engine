# Overview

NB for complete test results see ./oq_scaling_tests.md

DRIVER trying to find some configs that get us there with larger branches. current max (with shortener hack (BASE8836)) is 100 logic tree branches on **tryharder-ubuntu**

Observed while testing shortener hack that our process was dying after already havng done most of the work - OOM errors apparenently. See OOM failure example below.

### Test inputs

The latest NZSHM hazard reports - in this case a 108 Logic Tree Branch source model. all input are found in MEMORY_TESTING/inputs. NB this requires the BASE8836 shortener hack from this branch)

All tests performed on tryharder-ubuntu, a modern Ubuntu workstation with 64GB physical RAM and no user apps running.

### Test outputs

see A/B tests below and also MEMORY_TESTING/fil-result

### Findings

With some logging hacks I was able to isolate a one-line diagnostic (used for logging only) that was the culprit. to aid testing I wrapped this in a function with a switch for testing `I_WANNA_CHEW_MEMORY = True`.

and then used two memory analysis tools:

 - `psutil.Process().memory_info().rss` to get resident memory
 - **filprofiler** to show peak allocated memory
   `fil-profile run openquake/commands/__main__.py engine --run ..\pathto\job.ini`

Two comparison test below show that the allocated memory required for this one-liner can be large (67% in this case). In the MEMORY_TESTING/fil-result folder there are two html reports that show this clearly, and that memory is allocated here...

```
/home/chrisbc/DEV/GNS/opensha-modular/GEM/oq-engine/openquake/commonlib/source_reader.py:489 (__fromh5__)
        other = pickle.loads(gzip.decompress(blob)
```

### Questions/Suggestions

 - is the diagnotic needed at all?
 - if so, can it be done more efficiently?
 - and/or can it be configuration option, with default being disabled?
 - are there any other places that the `pickle.loads()` triggers excessive memory allocation?


## OOM failure example (w a 200 LTB source model)


at point of failure memory use jumped from 39GB to 63GB and swapping began. oq killed tasks


**INI**

```
[geometry]

sites_csv = nz_towns_4.csv

[logic_tree]

number_of_logic_tree_samples = 0

[erf]

concurrent_tasks = 1
rupture_mesh_spacing = 5
width_of_mfd_bin = 0.1

#rupture_mesh_spacing = 0.75
#width_of_mfd_bin = 0.1

complex_fault_mesh_spacing = 10.0
area_source_discretization = 10.0

[site_params]

#reference_vs30_value = 560.0
#reference_depth_to_1pt0km_per_sec = 162.0
#reference_depth_to_2pt5km_per_sec = 0.86

reference_vs30_value = 250
reference_depth_to_1pt0km_per_sec = 490.0
reference_depth_to_2pt5km_per_sec = 2.2

[calculation]

source_model_logic_tree_file = ./sources/source_model_200.xml
gsim_logic_tree_file = ./NZ_NSHM_logic_tree_set_2.xml
```

**LOG**
```
[2022-04-26 23:37:54 #31 INFO] chrisbc@tryharder-ubuntu running /home/chrisbc/DEV/GNS/opensha-modular/nzshm-runzi/docker/runzi-openquake/examples/25_BIG_CONFIG/job_wlg.ini [--hc=None]
[2022-04-26 23:37:54 #31 INFO] Using engine version 3.15.0-git02e259362a
[2022-04-26 23:37:55 #31 WARNING] Using 16 cores on tryharder-ubuntu
[2022-04-26 23:37:57 #31 INFO] Checksum of the inputs: 2123438359 (total size 122.32 MB)
[2022-04-26 23:37:57 #31 INFO] Reading the risk model if present
[2022-04-26 23:37:57 #31 INFO] Read N=4 hazard sites and L=377 hazard levels
[2022-04-26 23:38:06 #31 INFO] Validated source_model_200.xml in 8.91 seconds
[2022-04-26 23:38:06 #31 INFO] Total number of logic tree paths = 9_000
[2022-04-26 23:38:06 #31 INFO] There are 24830 non-unique source IDs
[2022-04-26 23:38:06 #31 INFO] Reading the source model(s) in parallel
[2022-04-26 23:38:07 #31 INFO] read_source_model   1% [17 submitted, 70 queued]
...
...
[2022-04-26 23:38:55 #31 INFO] read_source_model 100% [87 submitted, 0 queued]
[2022-04-26 23:38:55 #31 INFO] Mean time per core=40s, std=4.1s, min=34s, max=45s
[2022-04-26 23:38:55 #31 INFO] Received {'tot': '102.12 MB'} in 48 seconds from read_source_model
[2022-04-26 23:51:11 #31 INFO] Checking the sources bounding box
[2022-04-26 23:55:44 #31 INFO] Rupture floating factor = 3.2467825876467504
[2022-04-26 23:55:44 #31 INFO] Rupture spinning factor = 1.4454754508411667
[2022-04-26 23:55:45 #31 INFO] Using pointsource_distance={'default': '1000'}
[2022-04-26 23:55:46 #31 INFO] NMG = (2_016, 13, 5) = 1.0 MB
[2022-04-26 23:55:46 #31 INFO] Starting preclassical
[2022-04-27 00:00:49 #31 INFO] preclassical   1% [51 submitted, 0 queued]
...
...
[2022-04-27 00:01:07 #31 INFO] preclassical 100% [54 submitted, 0 queued]
[2022-04-27 00:01:07 #31 INFO] Mean time per core=35s, std=2.9s, min=30s, max=40s
[2022-04-27 00:01:07 #31 INFO] Received {'tot': '3.62 GB'} in 226 seconds from preclassical
[2022-04-27 00:01:07 #31 INFO] MultiFaultSource ruptures: 31_461
[2022-04-27 00:01:07 #31 INFO] PointSource ruptures: 1_265_182
[2022-04-27 00:01:07 #31 INFO] There are 46 groups and 24850 sources with len(trt_smrs)=199.53
[2022-04-27 00:01:07 #31 INFO] tot_weight=741_154, max_weight=741_154, num_sources=24_850
[2022-04-27 00:01:07 #31 INFO] Heaviest: <MultiFaultSource SW52ZXJzaW9uU29sdXRpb246MTAxMTgw:0, weight=20000.0>
[2022-04-27 00:05:06 #31 INFO] Storing 1.57 GB of CompositeSourceModel
[2022-04-27 00:05:08 #31 INFO] Requiring 58.91 KB for full ProbabilityMap of shape (5, 4, 377)
[2022-04-27 00:07:10 #31 INFO] grp_id->n_outs: [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
[2022-04-27 00:07:10 #31 INFO] Sent 46 classical tasks, 3.65 GB in 122 seconds
[2022-04-27 00:07:11 #31 INFO] classical   2% [46 submitted, 0 queued]
[2022-04-27 00:07:11 #31 INFO] classical   4% [46 submitted, 0 queued]
...
...
[2022-04-27 00:41:24 #31 INFO] classical 100% [46 submitted, 0 queued]
[2022-04-27 00:41:24 #31 INFO] Mean time per core=313s, std=472.0s, min=137s, max=2108s
[2022-04-27 00:41:24 #31 INFO] Received {'rup_data': '318.24 MB', 'pmap': '1.99 MB', 'source_data': '1.13 MB', 'cfactor': '6.38 KB', 'grp_id': '230 B', 'task_no': '230 B'} in 2053 seconds from classical
[2022-04-27 00:41:24 #31 INFO] There are 9000 realization(s)
[2022-04-27 00:41:24 #31 INFO] cfactor = 1_799_756/133_442 = 13.5
[2022-04-27 00:41:24 #31 INFO] There were 1 slow task(s)
Killed

real    68m44.663s
user    41m11.717s
sys     0m59.123s
(openquake) chrisbc@tryharder-ubuntu:~/DEV/GNS/opensha-modular/GEM/oq-engine$ /usr/lib/python3.8/multiprocessing/resource_tracker.py:216: UserWarning: resource_tracker: There appear to be 6 leaked semaphor
e objects to clean up at shutdown
  warnings.warn('resource_tracker: There appear to be %d '
```

# A/B TESTS

## 27_TAG_CONFIG source_model.xml (108) concurrent = 8 , I_WANNA_CHEW_MEMORY = False,  peak mem 7521.9 MiB


```
[2022-04-27 12:57:32 #54 INFO] Received {'rup_data': '324.88 MB', 'pmap': '1.13 MB', 'source_data': '1.13 MB', 'cfactor': '3.47 KB', 'grp_id': '125 B', 'task_no': '125 B'} in 1881 seconds from classical
[2022-04-27 12:57:40 #54 INFO] There are 4860 realization(s)
[2022-04-27 12:57:41 #54 INFO] cfactor = 1_777_807/122_538 = 14.5
[2022-04-27 12:57:41 #54 INFO] There were 1 slow task(s)
[2022-04-27 12:57:41 #54 INFO] report resident memory @ post_execute.1: 10.17173 GB
[2022-04-27 12:57:41 #54 INFO] begin post_classical
[2022-04-27 12:57:41 #54 INFO] individual_rlzs: True
[2022-04-27 12:57:41 #54 INFO] hstats 1 complete
[2022-04-27 12:57:41 #54 INFO] hstats 2 complete
[2022-04-27 12:57:41 #54 INFO] ct after adjustment: 60 from: 8
[2022-04-27 12:57:41 #54 INFO] dstore: <DataStore /home/chrisbc/oqdata/calc_54.hdf5 open>
[2022-04-27 12:57:41 #54 INFO] self.N: 4
[2022-04-27 12:57:41 #54 INFO] sites_per_task: 1
[2022-04-27 12:57:41 #54 INFO] Reading 381.27 KB of _poes/sid
[2022-04-27 12:57:41 #54 INFO] There are 96 slices of poes [24.0 per task]
[2022-04-27 12:57:41 #54 INFO] Producing 47.12 KB of hazard curves and 0 B of hazard maps
[2022-04-27 12:57:54 #54 INFO] postclassical  25% [4 submitted, 0 queued]
[2022-04-27 12:57:54 #54 INFO] postclassical  50% [4 submitted, 0 queued]
[2022-04-27 12:57:54 #54 INFO] postclassical  75% [4 submitted, 0 queued]
[2022-04-27 12:57:54 #54 INFO] postclassical 100% [4 submitted, 0 queued]
[2022-04-27 12:57:54 #54 INFO] Received {'hcurves-rlzs': '57.2 MB', 'hcurves-stats': '48.87 KB'} in 12 seconds from postclassical
[2022-04-27 12:57:54 #54 INFO] Saving hcurves-rlzs
[2022-04-27 12:57:54 #54 INFO] Saving hcurves-stats
[2022-04-27 12:57:54 #54 INFO] post_classical completed
[2022-04-27 12:57:54 #54 INFO] end post_execute
[2022-04-27 12:57:54 #54 INFO] Exposing the outputs to the database
rows => 108
[2022-04-27 12:57:55 #54 INFO] Stored 678.12 MB on /home/chrisbc/oqdata/calc_54.hdf5 in 2757 seconds
  id | name
  70 | Full Report
  71 | Hazard Curves
  72 | Realizations
=fil-profile= Preparing to write to fil-result/2022-04-27T12-58-23_002
=fil-profile= Wrote flamegraph to "fil-result/2022-04-27T12-58-23_002/peak-memory.svg"
=fil-profile= Wrote flamegraph to "fil-result/2022-04-27T12-58-23_002/peak-memory-reversed.svg"
=fil-profile= Wrote HTML report to fil-result/2022-04-27T12-58-23_002/index.html
=fil-profile= Trying to open the report in a browser. In some cases this may print error messages, especially on macOS. You can ignore those, it's just garbage output from the browser.
```

## 27_TAG_CONFIG source_model.xml (108) concurrent = 8 , I_WANNA_CHEW_MEMORY = True,  peak mem 13503.8

from nr = {name: len(dset['mag']) for name, dset in self.datastore.items() ALLOC 9.5GB 67%

see: fil-result/2022-04-27T23-04-57_333/index.html

```
Peak Tracked Memory Usage (13503.8 MiB)
Made with the Fil profiler. Try it on your code!

Function:         other = pickle.loads(gzip.decompress(blob)) (8,974,194,536 bytes, 63.74%)

openquake/commands/__main__.py:57 (<module>)
    oq()
openquake/commands/__main__.py:53 (oq)
    sap.run(commands, prog='oq')
/home/chrisbc/DEV/GNS/opensha-modular/GEM/oq-engine/openquake/baselib/sap.py:225 (run)
    return _run(parser(funcdict, **parserkw), argv)
/home/chrisbc/DEV/GNS/opensha-modular/GEM/oq-engine/openquake/baselib/sap.py:216 (_run)
    return func(**dic)
/home/chrisbc/DEV/GNS/opensha-modular/GEM/oq-engine/openquake/commands/engine.py:175 (main)
        run_jobs(jobs)
/home/chrisbc/DEV/GNS/opensha-modular/GEM/oq-engine/openquake/engine/engine.py:374 (run_jobs)
                run_calc(job)
/home/chrisbc/DEV/GNS/opensha-modular/GEM/oq-engine/openquake/engine/engine.py:274 (run_calc)
        calc.run(shutdown=True)
/home/chrisbc/DEV/GNS/opensha-modular/GEM/oq-engine/openquake/calculators/base.py:234 (run)
                    self.post_execute(self.result)
/home/chrisbc/DEV/GNS/opensha-modular/GEM/oq-engine/openquake/calculators/classical.py:585 (post_execute)
            evil_memory_allocation()
/home/chrisbc/DEV/GNS/opensha-modular/GEM/oq-engine/openquake/calculators/classical.py:575 (evil_memory_allocation)
            nr = {name: len(dset['mag']) for name, dset in self.datastore.items()
/home/chrisbc/DEV/GNS/opensha-modular/GEM/oq-engine/openquake/calculators/classical.py:575 (<dictcomp>)
            nr = {name: len(dset['mag']) for name, dset in self.datastore.items()
/usr/lib/python3.8/_collections_abc.py:744 (__iter__)
            yield (key, self._mapping[key])
/home/chrisbc/DEV/GNS/opensha-modular/GEM/oq-engine/openquake/commonlib/datastore.py:476 (__getitem__)
            val = self.hdf5[key]
/home/chrisbc/DEV/GNS/opensha-modular/GEM/oq-engine/openquake/baselib/hdf5.py:499 (__getitem__)
                obj.__fromh5__(h5obj, h5attrs)
/home/chrisbc/DEV/GNS/opensha-modular/GEM/oq-engine/openquake/commonlib/source_reader.py:489 (__fromh5__)
        other = pickle.loads(gzip.decompress(blob)
```

### Profiler:

```
$>fil-profile run openquake/commands/__main__.py engine --run ../../nzshm-runzi/docker/runzi-openquake/examples/27_TAG_CONFIG/job.ini
```

### LOG:


```
[2022-04-27 23:02:09 #55 INFO] classical 100% [25 submitted, 0 queued]
[2022-04-27 23:02:09 #55 INFO] Mean time per core=262s, std=427.8s, min=18s, max=1804s
[2022-04-27 23:02:10 #55 INFO] Received {'rup_data': '316.92 MB', 'pmap': '1.13 MB', 'source_data': '1.13 MB', 'cfactor': '3.47 KB', 'grp_id': '125 B', 'task_no': '125 B'} in 1901 seconds from classical
[2022-04-27 23:02:17 #55 INFO] There are 4860 realization(s)
[2022-04-27 23:02:18 #55 INFO] cfactor = 1_777_807/122_538 = 14.5
[2022-04-27 23:02:18 #55 INFO] There were 1 slow task(s)
[2022-04-27 23:02:18 #55 INFO] report resident memory @ post_execute.1: 10.166519 GB
rows => 108
[2022-04-27 23:04:15 #55 INFO] report resident memory @ post_execute.2: 10.307747 GB
[2022-04-27 23:04:15 #55 INFO] begin post_classical
[2022-04-27 23:04:15 #55 INFO] individual_rlzs: True
[2022-04-27 23:04:15 #55 INFO] hstats 1 complete
[2022-04-27 23:04:15 #55 INFO] hstats 2 complete
[2022-04-27 23:04:15 #55 INFO] ct after adjustment: 60 from: 8
[2022-04-27 23:04:15 #55 INFO] dstore: <DataStore /home/chrisbc/oqdata/calc_55.hdf5 open>
[2022-04-27 23:04:15 #55 INFO] self.N: 4
[2022-04-27 23:04:15 #55 INFO] sites_per_task: 1
[2022-04-27 23:04:15 #55 INFO] Reading 381.27 KB of _poes/sid
[2022-04-27 23:04:15 #55 INFO] There are 96 slices of poes [24.0 per task]
[2022-04-27 23:04:16 #55 INFO] Producing 47.12 KB of hazard curves and 0 B of hazard maps
[2022-04-27 23:04:28 #55 INFO] postclassical  25% [4 submitted, 0 queued]
[2022-04-27 23:04:28 #55 INFO] postclassical  50% [4 submitted, 0 queued]
[2022-04-27 23:04:28 #55 INFO] postclassical  75% [4 submitted, 0 queued]
[2022-04-27 23:04:28 #55 INFO] postclassical 100% [4 submitted, 0 queued]
[2022-04-27 23:04:28 #55 INFO] Received {'hcurves-rlzs': '57.2 MB', 'hcurves-stats': '48.87 KB'} in 12 seconds from postclassical
[2022-04-27 23:04:28 #55 INFO] Saving hcurves-rlzs
[2022-04-27 23:04:28 #55 INFO] Saving hcurves-stats
[2022-04-27 23:04:28 #55 INFO] post_classical completed
[2022-04-27 23:04:28 #55 INFO] end post_execute
[2022-04-27 23:04:29 #55 INFO] Exposing the outputs to the database
rows => 108
[2022-04-27 23:04:29 #55 INFO] Stored 678.14 MB on /home/chrisbc/oqdata/calc_55.hdf5 in 2896 seconds
  id | name
  73 | Full Report
  74 | Hazard Curves
  75 | Realizations
=fil-profile= Preparing to write to fil-result/2022-04-27T23-04-57_333
=fil-profile= Wrote flamegraph to "fil-result/2022-04-27T23-04-57_333/peak-memory.svg"
=fil-profile= Wrote flamegraph to "fil-result/2022-04-27T23-04-57_333/peak-memory-reversed.svg"
=fil-profile= Wrote HTML report to fil-result/2022-04-27T23-04-57_333/index.html
=fil-profile= Trying to open the report in a browser. In some cases this may print error messages, especially on macOS. You can ignore those, it's just garbage output from the browser.
```