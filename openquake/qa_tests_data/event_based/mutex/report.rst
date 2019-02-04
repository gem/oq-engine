Event Based QA Test, Case 1
===========================

============== ===================
checksum32     3,529,984,501      
date           2019-02-03T09:38:40
engine_version 3.4.0-gite8c42e513a
============== ===================

num_sites = 1, num_levels = 46

Parameters
----------
=============================== ==================
calculation_mode                'event_based'     
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              50.0              
ses_per_logic_tree_path         2000              
truncation_level                2.0               
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                1.0               
area_source_discretization      20.0              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     42                
master_seed                     0                 
ses_seed                        1066              
=============================== ==================

Input files
-----------
======================= ========================
Name                    File                    
======================= ========================
gsim_logic_tree         `gmmLT.xml <gmmLT.xml>`_
job_ini                 `job.ini <job.ini>`_    
source_model_logic_tree `ssmLT.xml <ssmLT.xml>`_
======================= ========================

Slowest sources
---------------
====== ========= ==== ====== ====== ============ ========= ========== ========= ========= ======
grp_id source_id code gidx1  gidx2  num_ruptures calc_time split_time num_sites num_split weight
====== ========= ==== ====== ====== ============ ========= ========== ========= ========= ======
0      case_10   N    29,255 32,080 1            0.0       0.0        0.0       1         0.0   
0      case_09   N    28,021 29,255 1            0.0       0.0        0.0       1         0.0   
0      case_08   N    21,872 28,021 1            0.0       0.0        0.0       1         0.0   
0      case_07   N    17,050 21,872 1            0.0       0.0        0.0       1         0.0   
0      case_06   N    12,124 17,050 1            0.0       0.0        0.0       1         0.0   
0      case_05   N    8,525  12,124 1            0.0       0.0        0.0       1         0.0   
0      case_04   N    5,132  8,525  1            0.0       0.0        0.0       1         0.0   
0      case_03   N    3,599  5,132  1            0.0       0.0        0.0       1         0.0   
0      case_02   N    1,207  3,599  1            0.0       0.0        0.0       1         0.0   
0      case_01   N    0      1,207  1            0.0       0.0        0.0       1         0.0   
====== ========= ==== ====== ====== ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
N    0.0       10    
==== ========= ======

Duplicated sources
------------------
Found 0 source(s) with the same ID and 0 true duplicate(s)

Information about the tasks
---------------------------
================== ======= ====== ======= ======= =======
operation-duration mean    stddev min     max     outputs
read_source_models 0.14282 NaN    0.14282 0.14282 1      
only_filter        0.00360 NaN    0.00360 0.00360 1      
================== ======= ====== ======= ======= =======

Data transfer
-------------
================== ========================================= =========
task               sent                                      received 
read_source_models converter=313 B fnames=107 B              756.09 KB
only_filter        srcs=755.63 KB srcfilter=253 B dummy=14 B 756 KB   
================== ========================================= =========

Slowest operations
------------------
======================== ======== ========= ======
operation                time_sec memory_mb counts
======================== ======== ========= ======
total read_source_models 0.14282  5.31641   1     
total only_filter        0.00360  1.33984   1     
======================== ======== ========= ======