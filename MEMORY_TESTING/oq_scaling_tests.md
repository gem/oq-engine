# TESTS

trying to find some configs that get us there with larger branches. current max (with shortener hack (BASE8836)) is 100 on **tryharder-ubuntu**

## OOM failure example (LTB 200)

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


# concurrent = 0

```
[2022-04-27 01:43:06 #36 INFO] read_source_model  96% [87 submitted, 0 queued]
[2022-04-27 01:43:06 #36 INFO] read_source_model  97% [87 submitted, 0 queued]
[2022-04-27 01:43:06 #36 INFO] read_source_model  98% [87 submitted, 0 queued]
[2022-04-27 01:43:06 #36 INFO] read_source_model 100% [87 submitted, 0 queued]
[2022-04-27 01:43:06 #36 INFO] Received {'tot': '102.12 MB'} in 399 seconds from read_source_model
```
bailed 4 times slower



# concurrent = 1

```
[2022-04-27 02:34:30 #37 INFO] classical  97% [46 submitted, 0 queued]
[2022-04-27 03:01:26 #37 INFO] classical 100% [46 submitted, 0 queued]
[2022-04-27 03:01:26 #37 INFO] Mean time per core=329s, std=496.2s, min=144s, max=2211s
[2022-04-27 03:01:26 #37 INFO] Received {'rup_data': '331.1 MB', 'pmap': '1.99 MB', 'source_data': '1.13 MB', 'cfactor': '6.38 KB', 'grp_id': '230 B', 'task_no': '230 B'} in 2165 seconds from classical
[2022-04-27 03:01:27 #37 INFO] There are 9000 realization(s)
[2022-04-27 03:01:27 #37 INFO] cfactor = 1_799_756/133_442 = 13.5
[2022-04-27 03:01:27 #37 INFO] There were 1 slow task(s)
Killed

real    68m24.887s
user    41m34.427s
sys     0m58.419s
```

# concurrent = 1 (commented code blocks)

completed in 65m

outputs in ./SLT001_1

# source_model_10.xml concurrent = 1

```
[2022-04-27 06:13:10 #45 INFO] Received {'rup_data': '313.83 MB', 'source_data': '1.12 MB', 'pmap': '489.42 KB', 'cfactor': '1.8 KB', 'grp_id': '65 B', 'task_no': '65 B'} in 2161 seconds from classical
[2022-04-27 06:13:11 #45 INFO] There are 450 realization(s)
[2022-04-27 06:13:11 #45 INFO] cfactor = 1_750_333/103_405 = 16.9
[2022-04-27 06:13:11 #45 INFO] There were 1 slow task(s)
[2022-04-27 06:13:11 #45 INFO] report resident memory @ post_execute.1: 1.588436 GB
rows => 10
[2022-04-27 06:13:17 #45 INFO] report resident memory @ post_execute.2: 1.618999 GB
[2022-04-27 06:13:17 #45 INFO] begin post_classical
[2022-04-27 06:13:17 #45 INFO] individual_rlzs: True
[2022-04-27 06:13:17 #45 INFO] hstats 1 complete
[2022-04-27 06:13:17 #45 INFO] hstats 2 complete
[2022-04-27 06:13:17 #45 INFO] ct after adjustment: 1 from: 1
[2022-04-27 06:13:17 #45 INFO] dstore: <DataStore /home/chrisbc/oqdata/calc_45.hdf5 open>
[2022-04-27 06:13:17 #45 INFO] self.N: 4
[2022-04-27 06:13:17 #45 INFO] sites_per_task: 4
[2022-04-27 06:13:17 #45 INFO] Reading 158.11 KB of _poes/sid
[2022-04-27 06:13:17 #45 INFO] There are 1 slices of poes [1.0 per task]
[2022-04-27 06:13:17 #45 INFO] Producing 47.12 KB of hazard curves and 0 B of hazard maps
[2022-04-27 06:13:18 #45 INFO] postclassical 100% [1 submitted, 0 queued]
[2022-04-27 06:13:18 #45 INFO] Received {'hcurves-rlzs': '5.27 MB', 'hcurves-stats': '48.05 KB'} in 0 seconds from postclassical
[2022-04-27 06:13:18 #45 INFO] Saving hcurves-rlzs
[2022-04-27 06:13:18 #45 INFO] Saving hcurves-stats
[2022-04-27 06:13:18 #45 INFO] post_classical completed
[2022-04-27 06:13:18 #45 INFO] end post_execute
[2022-04-27 06:13:18 #45 INFO] Exposing the outputs to the database
rows => 10
[2022-04-27 06:13:18 #45 INFO] Stored 267.1 MB on /home/chrisbc/oqdata/calc_45.hdf5 in 2233 seconds
  id | name
  47 | Full Report
  48 | Hazard Curves
  49 | Realizations

real    37m16.999s
user    49m9.638s
sys     0m15.424s
```

# source_model_10.xml concurrent = 8

```
[2022-04-27 06:34:26 #46 INFO] Mean time per core=149s, std=202.2s, min=6s, max=682s
[2022-04-27 06:34:26 #46 INFO] Received {'rup_data': '310.36 MB', 'source_data': '1.12 MB', 'pmap': '822.24 KB', 'cfactor': '2.63 KB', 'grp_id': '95 B', 'task_no': '95 B'} in 697 seconds from classical
[2022-04-27 06:34:27 #46 INFO] There are 450 realization(s)
[2022-04-27 06:34:27 #46 INFO] cfactor = 1_750_333/141_315 = 12.4
[2022-04-27 06:34:27 #46 INFO] There were 1 slow task(s)
[2022-04-27 06:34:27 #46 INFO] report resident memory @ post_execute.1: 1.187737 GB
rows => 10
[2022-04-27 06:34:34 #46 INFO] report resident memory @ post_execute.2: 1.219414 GB
[2022-04-27 06:34:34 #46 INFO] begin post_classical
[2022-04-27 06:34:34 #46 INFO] individual_rlzs: True
[2022-04-27 06:34:34 #46 INFO] hstats 1 complete
[2022-04-27 06:34:34 #46 INFO] hstats 2 complete
[2022-04-27 06:34:34 #46 INFO] ct after adjustment: 60 from: 8
[2022-04-27 06:34:34 #46 INFO] dstore: <DataStore /home/chrisbc/oqdata/calc_46.hdf5 open>
[2022-04-27 06:34:34 #46 INFO] self.N: 4
[2022-04-27 06:34:34 #46 INFO] sites_per_task: 1
[2022-04-27 06:34:34 #46 INFO] Reading 158.11 KB of _poes/sid
[2022-04-27 06:34:34 #46 INFO] There are 52 slices of poes [13.0 per task]
[2022-04-27 06:34:34 #46 INFO] Producing 47.12 KB of hazard curves and 0 B of hazard maps
[2022-04-27 06:34:35 #46 INFO] postclassical  25% [4 submitted, 0 queued]
[2022-04-27 06:34:35 #46 INFO] postclassical  50% [4 submitted, 0 queued]
[2022-04-27 06:34:35 #46 INFO] postclassical  75% [4 submitted, 0 queued]
[2022-04-27 06:34:35 #46 INFO] postclassical 100% [4 submitted, 0 queued]
[2022-04-27 06:34:35 #46 INFO] Received {'hcurves-rlzs': '5.3 MB', 'hcurves-stats': '48.87 KB'} in 0 seconds from postclassical
[2022-04-27 06:34:35 #46 INFO] Saving hcurves-rlzs
[2022-04-27 06:34:35 #46 INFO] Saving hcurves-stats
[2022-04-27 06:34:35 #46 INFO] post_classical completed
[2022-04-27 06:34:35 #46 INFO] end post_execute
[2022-04-27 06:34:35 #46 INFO] Exposing the outputs to the database
rows => 10
[2022-04-27 06:34:35 #46 INFO] Stored 266.86 MB on /home/chrisbc/oqdata/calc_46.hdf5 in 769 seconds
  id | name
  50 | Full Report
  51 | Hazard Curves
  52 | Realizations

real    12m53.151s
user    45m51.773s
sys     0m15.817s
```

# source_model_100.xml concurrent = 8

2022-04-27 07:12:48 #47 INFO] Mean time per core=227s, std=353.8s, min=44s, max=1407s
[2022-04-27 07:12:48 #47 INFO] Received {'rup_data': '316.85 MB', 'pmap': '1.13 MB', 'source_data': '1
.13 MB', 'cfactor': '3.47 KB', 'grp_id': '125 B', 'task_no': '125 B'} in 1425 seconds from classical
[2022-04-27 07:12:48 #47 INFO] There are 4500 realization(s)
[2022-04-27 07:12:48 #47 INFO] cfactor = 1_774_976/121_060 = 14.7
[2022-04-27 07:12:48 #47 INFO] There were 1 slow task(s)
[2022-04-27 07:12:48 #47 INFO] report resident memory @ post_execute.1: 7.353424 GB
rows => 100
[2022-04-27 07:13:42 #47 INFO] report resident memory @ post_execute.2: 7.428028 GB
[2022-04-27 07:13:42 #47 INFO] begin post_classical
[2022-04-27 07:13:42 #47 INFO] individual_rlzs: True
[2022-04-27 07:13:42 #47 INFO] hstats 1 complete
[2022-04-27 07:13:42 #47 INFO] hstats 2 complete
[2022-04-27 07:13:42 #47 INFO] ct after adjustment: 60 from: 8
[2022-04-27 07:13:43 #47 INFO] dstore: <DataStore /home/chrisbc/oqdata/calc_47.hdf5 open>
[2022-04-27 07:13:43 #47 INFO] self.N: 4
[2022-04-27 07:13:43 #47 INFO] sites_per_task: 1
[2022-04-27 07:13:43 #47 INFO] Reading 382.89 KB of _poes/sid
[2022-04-27 07:13:43 #47 INFO] There are 96 slices of poes [24.0 per task]
[2022-04-27 07:13:43 #47 INFO] Producing 47.12 KB of hazard curves and 0 B of hazard maps
[2022-04-27 07:13:46 #47 INFO] postclassical  25% [4 submitted, 0 queued]
[2022-04-27 07:13:46 #47 INFO] postclassical  50% [4 submitted, 0 queued]
[2022-04-27 07:13:46 #47 INFO] postclassical  75% [4 submitted, 0 queued]
[2022-04-27 07:13:47 #47 INFO] postclassical 100% [4 submitted, 0 queued]
[2022-04-27 07:13:47 #47 INFO] Received {'hcurves-rlzs': '52.97 MB', 'hcurves-stats': '48.87 KB'} in 3
 seconds from postclassical
[2022-04-27 07:13:47 #47 INFO] Saving hcurves-rlzs
[2022-04-27 07:13:47 #47 INFO] Saving hcurves-stats
[2022-04-27 07:13:47 #47 INFO] post_classical completed
[2022-04-27 07:13:47 #47 INFO] end post_execute
[2022-04-27 07:13:47 #47 INFO] Exposing the outputs to the database
rows => 100
[2022-04-27 07:13:47 #47 INFO] Stored 662.4 MB on /home/chrisbc/oqdata/calc_47.hdf5 in 1980 seconds
  id | name
  53 | Full Report
  54 | Hazard Curves
  55 | Realizations

real    33m5.536s
user    82m0.309s
sys     0m35.313s

# NZSEE fil-profile test 1 baseline (peak memory 1032.9 M)

```
2022-04-27 07:30:16 #49 INFO] Received {'pmap': '453.98 KB', 'rup_data': '61.79 KB', 'source_data': '2.38 KB', 'cfactor': '1.66 KB', 'grp_id': '60 B', 'task_no': '60 B'} in 6 seconds from classical
[2022-04-27 07:30:16 #49 INFO] There are 36 realization(s)
[2022-04-27 07:30:16 #49 INFO] cfactor = 708/507 = 1.4
[2022-04-27 07:30:16 #49 INFO] report resident memory @ post_execute.1: 1.185001 GB
rows => 12
[2022-04-27 07:30:21 #49 INFO] report resident memory @ post_execute.2: 1.361633 GB
[2022-04-27 07:30:21 #49 INFO] begin post_classical
[2022-04-27 07:30:21 #49 INFO] individual_rlzs: True
[2022-04-27 07:30:21 #49 INFO] hstats 1 complete
[2022-04-27 07:30:21 #49 INFO] hstats 2 complete
[2022-04-27 07:30:21 #49 INFO] ct after adjustment: 60 from: 10
[2022-04-27 07:30:21 #49 INFO] dstore: <DataStore /home/chrisbc/oqdata/calc_49.hdf5 open>
[2022-04-27 07:30:21 #49 INFO] self.N: 1
[2022-04-27 07:30:21 #49 INFO] sites_per_task: 1
[2022-04-27 07:30:22 #49 INFO] Reading 214.2 KB of _poes/sid
[2022-04-27 07:30:22 #49 INFO] There are 1 slices of poes [1.0 per task]
[2022-04-27 07:30:22 #49 INFO] Producing 50 KB of hazard curves and 1.5 KB of hazard maps
[2022-04-27 07:30:22 #49 INFO] postclassical 100% [1 submitted, 0 queued]
[2022-04-27 07:30:22 #49 INFO] Received {'hcurves-rlzs': '452.69 KB', 'hcurves-stats': '50.44 KB', 'hmaps-rlzs': '9.02 KB', 'hmaps-stats': '1.18 KB'} in 0 seconds from postclassical
[2022-04-27 07:30:22 #49 INFO] Saving hcurves-rlzs
[2022-04-27 07:30:22 #49 INFO] Saving hcurves-stats
[2022-04-27 07:30:22 #49 INFO] Saving hmaps-rlzs
[2022-04-27 07:30:22 #49 INFO] Saving hmaps-stats
[2022-04-27 07:30:22 #49 INFO] The maximum hazard map values are {'PGA': 3.2016869, 'SA(0.1)': 5.0, 'SA(0.2)': 5.0, 'SA(0.5)': 5.0, 'SA(0.75)': 5.0, 'SA(1.0)': 5.0, 'SA(1.25)': 4.3833046, 'SA(1.5)': 3.5999203, 'SA(1.75)': 3.0934577, 'SA(2.0)': 2.7095222, 'SA(2.5)': 1.8772827, 'SA(3.0)': 1.5123229, 'SA(4.0)': 1.0378326, 'SA(5.0)': 0.811221, 'SA(6.0)': 0.5870751, 'SA(7.5)': 0.4477517}
[2022-04-27 07:30:22 #49 INFO] post_classical completed
[2022-04-27 07:30:22 #49 INFO] end post_execute
[2022-04-27 07:30:22 #49 INFO] Exposing the outputs to the database
rows => 12
[2022-04-27 07:30:22 #49 INFO] Stored 63.64 MB on /home/chrisbc/oqdata/calc_49.hdf5 in 68 seconds
  id | name
  56 | Full Report
  57 | Hazard Curves
  58 | Realizations
  59 | Uniform Hazard Spectra
=fil-profile= Preparing to write to fil-result/2022-04-27T07-30-24_276
=fil-profile= Wrote flamegraph to "fil-result/2022-04-27T07-30-24_276/peak-memory.svg"
=fil-profile= Wrote flamegraph to "fil-result/2022-04-27T07-30-24_276/peak-memory-reversed.svg"
=fil-profile= Wrote HTML report to fil-result/2022-04-27T07-30-24_276/index.html
=fil-profile= Trying to open the report in a browser. In some cases this may print error messages, especially on macOS. You can ignore those, it's just garbage output from the browser.
```

# NZSEE fil-profile test 2 nr commented out (peak mem 650.4 MiB)

```
[2022-04-27 07:35:53 #50 INFO] Received {'pmap': '453.98 KB', 'rup_data': '61.79 KB', 'source_data': '2.38 KB', 'cfactor': '1.66 KB', 'grp_id': '60 B', 'task_no': '60 B'} in 6 seconds from classical
[2022-04-27 07:35:53 #50 INFO] There are 36 realization(s)
[2022-04-27 07:35:53 #50 INFO] cfactor = 708/507 = 1.4
[2022-04-27 07:35:53 #50 INFO] report resident memory @ post_execute.1: 1.184643 GB
[2022-04-27 07:35:53 #50 INFO] begin post_classical
[2022-04-27 07:35:53 #50 INFO] individual_rlzs: True
[2022-04-27 07:35:53 #50 INFO] hstats 1 complete
[2022-04-27 07:35:53 #50 INFO] hstats 2 complete
[2022-04-27 07:35:53 #50 INFO] ct after adjustment: 60 from: 10
[2022-04-27 07:35:53 #50 INFO] dstore: <DataStore /home/chrisbc/oqdata/calc_50.hdf5 open>
[2022-04-27 07:35:53 #50 INFO] self.N: 1
[2022-04-27 07:35:53 #50 INFO] sites_per_task: 1
[2022-04-27 07:35:54 #50 INFO] Reading 214.2 KB of _poes/sid
[2022-04-27 07:35:54 #50 INFO] There are 1 slices of poes [1.0 per task]
[2022-04-27 07:35:54 #50 INFO] Producing 50 KB of hazard curves and 1.5 KB of hazard maps
[2022-04-27 07:35:54 #50 INFO] postclassical 100% [1 submitted, 0 queued]
[2022-04-27 07:35:54 #50 INFO] Received {'hcurves-rlzs': '452.69 KB', 'hcurves-stats': '50.44 KB', 'hmaps-rlzs': '9.02 KB', 'hmaps-stats': '1.18 KB'} in 0 seconds from postclassical
[2022-04-27 07:35:54 #50 INFO] Saving hcurves-rlzs
[2022-04-27 07:35:54 #50 INFO] Saving hcurves-stats
[2022-04-27 07:35:54 #50 INFO] Saving hmaps-rlzs
[2022-04-27 07:35:54 #50 INFO] Saving hmaps-stats
[2022-04-27 07:35:54 #50 INFO] The maximum hazard map values are {'PGA': 3.2016869, 'SA(0.1)': 5.0, 'SA(0.2)': 5.0, 'SA(0.5)': 5.0, 'SA(0.75)': 5.0, 'SA(1.0)': 5.0, 'SA(1.25)': 4.3833046, 'SA(1.5)': 3.5999203, 'SA(1.75)': 3.0934577, 'SA(2.0)': 2.7095222, 'SA(2.5)': 1.8772827, 'SA(3.0)': 1.5123229, 'SA(4.0)': 1.0378326, 'SA(5.0)': 0.811221, 'SA(6.0)': 0.5870751, 'SA(7.5)': 0.4477517}
[2022-04-27 07:35:54 #50 INFO] post_classical completed
[2022-04-27 07:35:54 #50 INFO] end post_execute
[2022-04-27 07:35:54 #50 INFO] Exposing the outputs to the database
rows => 12
[2022-04-27 07:35:55 #50 INFO] Stored 63.64 MB on /home/chrisbc/oqdata/calc_50.hdf5 in 62 seconds
  id | name
  60 | Full Report
  61 | Hazard Curves
  62 | Realizations
  63 | Uniform Hazard Spectra
=fil-profile= Preparing to write to fil-result/2022-04-27T07-35-56_188
=fil-profile= Wrote flamegraph to "fil-result/2022-04-27T07-35-56_188/peak-memory.svg"
=fil-profile= Wrote flamegraph to "fil-result/2022-04-27T07-35-56_188/peak-memory-reversed.svg"
=fil-profile= Wrote HTML report to fil-result/2022-04-27T07-35-56_188/index.html
=fil-profile= Trying to open the report in a browser. In some cases this may print error messages, especially on macOS. You can ignore those, it's just garbage output from the browser.
```

## source_model_10.xml concurrent = 8 , I_WANNA_CHEW_MEMORY = True,  peak mem 1856.0 MiB

'''
22.24 KB', 'cfactor': '2.63 KB', 'grp_id': '95 B', 'task_no': '95 B'} in 784 seconds from classical
[2022-04-27 08:09:25 #51 INFO] There are 450 realization(s)
[2022-04-27 08:09:25 #51 INFO] cfactor = 1_750_333/141_315 = 12.4
[2022-04-27 08:09:25 #51 INFO] There were 1 slow task(s)
[2022-04-27 08:09:25 #51 INFO] report resident memory @ post_execute.1: 2.516701 GB
rows => 10
[2022-04-27 08:09:37 #51 INFO] report resident memory @ post_execute.2: 2.538609 GB
[2022-04-27 08:09:37 #51 INFO] begin post_classical
[2022-04-27 08:09:37 #51 INFO] individual_rlzs: True
[2022-04-27 08:09:37 #51 INFO] hstats 1 complete
[2022-04-27 08:09:37 #51 INFO] hstats 2 complete
[2022-04-27 08:09:37 #51 INFO] ct after adjustment: 60 from: 8
[2022-04-27 08:09:37 #51 INFO] dstore: <DataStore /home/chrisbc/oqdata/calc_51.hdf5 open>
[2022-04-27 08:09:37 #51 INFO] self.N: 4
[2022-04-27 08:09:37 #51 INFO] sites_per_task: 1
[2022-04-27 08:09:37 #51 INFO] Reading 158.11 KB of _poes/sid
[2022-04-27 08:09:37 #51 INFO] There are 52 slices of poes [13.0 per task]
[2022-04-27 08:09:37 #51 INFO] Producing 47.12 KB of hazard curves and 0 B of hazard maps
[2022-04-27 08:09:39 #51 INFO] postclassical  25% [4 submitted, 0 queued]
[2022-04-27 08:09:39 #51 INFO] postclassical  50% [4 submitted, 0 queued]
[2022-04-27 08:09:39 #51 INFO] postclassical  75% [4 submitted, 0 queued]
[2022-04-27 08:09:39 #51 INFO] postclassical 100% [4 submitted, 0 queued]
[2022-04-27 08:09:39 #51 INFO] Received {'hcurves-rlzs': '5.3 MB', 'hcurves-stats': '48.87 KB'} in 1 seconds from postclassical
[2022-04-27 08:09:39 #51 INFO] Saving hcurves-rlzs
[2022-04-27 08:09:39 #51 INFO] Saving hcurves-stats
[2022-04-27 08:09:39 #51 INFO] post_classical completed
[2022-04-27 08:09:39 #51 INFO] end post_execute
[2022-04-27 08:09:39 #51 INFO] Exposing the outputs to the database
rows => 10
[2022-04-27 08:09:39 #51 INFO] Stored 266.86 MB on /home/chrisbc/oqdata/calc_51.hdf5 in 896 seconds
  id | name
  64 | Full Report
  65 | Hazard Curves
  66 | Realizations
=fil-profile= Preparing to write to fil-result/2022-04-27T08-09-42_557
=fil-profile= Wrote flamegraph to "fil-result/2022-04-27T08-09-42_557/peak-memory.svg"
=fil-profile= Wrote flamegraph to "fil-result/2022-04-27T08-09-42_557/peak-memory-reversed.svg"
=fil-profile= Wrote HTML report to fil-result/2022-04-27T08-09-42_557/index.html
=fil-profile= Trying to open the report in a browser. In some cases this may print error messages, especially on macOS. You can ignore those, it's just garbage output from the browser.
```

## source_model_10.xml concurrent = 8 , I_WANNA_CHEW_MEMORY = False,  peak mem 1856.0 MiB


```
[2022-04-27 08:31:18 #52 INFO] There are 450 realization(s)
[2022-04-27 08:31:18 #52 INFO] cfactor = 1_750_333/141_315 = 12.4
[2022-04-27 08:31:18 #52 INFO] There were 1 slow task(s)
[2022-04-27 08:31:18 #52 INFO] report resident memory @ post_execute.1: 2.512119 GB
[2022-04-27 08:31:18 #52 INFO] begin post_classical
[2022-04-27 08:31:18 #52 INFO] individual_rlzs: True
[2022-04-27 08:31:18 #52 INFO] hstats 1 complete
[2022-04-27 08:31:18 #52 INFO] hstats 2 complete
[2022-04-27 08:31:18 #52 INFO] ct after adjustment: 60 from: 8
[2022-04-27 08:31:18 #52 INFO] dstore: <DataStore /home/chrisbc/oqdata/calc_52.hdf5 open>
[2022-04-27 08:31:18 #52 INFO] self.N: 4
[2022-04-27 08:31:18 #52 INFO] sites_per_task: 1
[2022-04-27 08:31:18 #52 INFO] Reading 158.11 KB of _poes/sid
[2022-04-27 08:31:18 #52 INFO] There are 52 slices of poes [13.0 per task]
[2022-04-27 08:31:19 #52 INFO] Producing 47.12 KB of hazard curves and 0 B of hazard maps
[2022-04-27 08:31:20 #52 INFO] postclassical  25% [4 submitted, 0 queued]
[2022-04-27 08:31:20 #52 INFO] postclassical  50% [4 submitted, 0 queued]
[2022-04-27 08:31:20 #52 INFO] postclassical  75% [4 submitted, 0 queued]
[2022-04-27 08:31:20 #52 INFO] postclassical 100% [4 submitted, 0 queued]
[2022-04-27 08:31:20 #52 INFO] Received {'hcurves-rlzs': '5.3 MB', 'hcurves-stats': '48.87 KB'} in 1 seconds from postclassical
[2022-04-27 08:31:20 #52 INFO] Saving hcurves-rlzs
[2022-04-27 08:31:20 #52 INFO] Saving hcurves-stats
[2022-04-27 08:31:20 #52 INFO] post_classical completed
[2022-04-27 08:31:20 #52 INFO] end post_execute
[2022-04-27 08:31:20 #52 INFO] Exposing the outputs to the database
rows => 10
[2022-04-27 08:31:21 #52 INFO] Stored 266.89 MB on /home/chrisbc/oqdata/calc_52.hdf5 in 924 seconds
  id | name
  67 | Full Report
  68 | Hazard Curves
  69 | Realizations
=fil-profile= Preparing to write to fil-result/2022-04-27T08-31-21_047
=fil-profile= Wrote flamegraph to "fil-result/2022-04-27T08-31-21_047/peak-memory.svg"
=fil-profile= Wrote flamegraph to "fil-result/2022-04-27T08-31-21_047/peak-memory-reversed.svg"
=fil-profile= Wrote HTML report to fil-result/2022-04-27T08-31-21_047/index.html
=fil-profile= Trying to open the report in a browser. In some cases this may print error messages, especially on macOS. You can ignore those, it's just garbage output from the browser.
```

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