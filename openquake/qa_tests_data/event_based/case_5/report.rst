Germany_SHARE Combined Model event_based
========================================

============== ===================
checksum32     1,250,935,976      
date           2019-01-20T07:38:02
engine_version 3.4.0-git452d0c6835
============== ===================

num_sites = 100, num_levels = 1

Parameters
----------
=============================== =================
calculation_mode                'event_based'    
number_of_logic_tree_samples    0                
maximum_distance                {'default': 80.0}
investigation_time              30.0             
ses_per_logic_tree_path         1                
truncation_level                3.0              
rupture_mesh_spacing            5.0              
complex_fault_mesh_spacing      5.0              
width_of_mfd_bin                0.1              
area_source_discretization      18.0             
ground_motion_correlation_model None             
minimum_intensity               {}               
random_seed                     42               
master_seed                     0                
ses_seed                        23               
=============================== =================

Input files
-----------
======================= ==============================================================================
Name                    File                                                                          
======================= ==============================================================================
gsim_logic_tree         `complete_gmpe_logic_tree.xml <complete_gmpe_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                                          
sites                   `sites.csv <sites.csv>`_                                                      
source_model_logic_tree `combined_logic-tree-source-model.xml <combined_logic-tree-source-model.xml>`_
======================= ==============================================================================

Slowest sources
---------------
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======
grp_id source_id code gidx1 gidx2 num_ruptures calc_time split_time num_sites num_split weight
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======
0      1         A    0     4     7            0.0       0.0        0.0       1         0.0   
0      2         A    4     8     7            0.0       0.0        0.0       1         0.0   
1      1339      A    8     18    168          0.0       0.0        0.0       1         0.0   
1      19        S    18    81    349          0.0       0.0        0.0       1         0.0   
1      20        S    81    100   31           0.0       0.0        0.0       1         0.0   
1      21        S    100   109   7            0.0       0.0        0.0       1         0.0   
1      22        S    109   123   34           0.0       0.0        0.0       1         0.0   
1      246       A    123   129   156          0.0       0.0        0.0       1         0.0   
1      247       A    129   135   156          0.0       0.0        0.0       1         0.0   
1      248       A    135   146   384          0.0       0.0        0.0       1         0.0   
1      249       A    146   157   384          0.0       0.0        0.0       1         0.0   
1      250       A    157   168   384          0.0       0.0        0.0       1         0.0   
1      257       A    168   181   96           0.0       0.0        0.0       1         0.0   
1      258       A    181   194   96           0.0       0.0        0.0       1         0.0   
1      259       A    194   207   96           0.0       0.0        0.0       1         0.0   
1      263       A    207   219   1,022        0.0       0.0        0.0       1         0.0   
1      264       A    219   231   1,022        0.0       0.0        0.0       1         0.0   
2      101622    P    231   232   39           0.0       0.0        0.0       0         0.0   
2      101623    P    232   233   36           0.0       0.0        0.0       0         0.0   
3      323839    P    233   234   6            0.0       0.0        0.0       0         0.0   
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
A    0.0       13    
P    0.0       51    
S    0.0       4     
==== ========= ======

Duplicated sources
------------------
Found 0 source(s) with the same ID and 0 true duplicate(s)

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
read_source_models 0.03689 0.04761 0.00456 0.09156 3      
split_filter       0.02208 NaN     0.02208 0.02208 1      
================== ======= ======= ======= ======= =======

Data transfer
-------------
================== ======================================== ========
task               sent                                     received
read_source_models converter=1.14 KB fnames=383 B           45.51 KB
split_filter       srcs=45.22 KB srcfilter=253 B dummy=14 B 41.92 KB
================== ======================================== ========

Slowest operations
------------------
======================== ======== ========= ======
operation                time_sec memory_mb counts
======================== ======== ========= ======
total read_source_models 0.11066  0.84375   3     
total only_filter        0.02208  2.08984   1     
======================== ======== ========= ======