QA test for disaggregation case_2
=================================

============== ===================
checksum32     3,620,311,746      
date           2019-01-27T08:28:54
engine_version 3.4.0-git7f110aaa0b
============== ===================

num_sites = 2, num_levels = 1

Parameters
----------
=============================== =================
calculation_mode                'disaggregation' 
number_of_logic_tree_samples    0                
maximum_distance                {'default': 80.0}
investigation_time              1.0              
ses_per_logic_tree_path         1                
truncation_level                3.0              
rupture_mesh_spacing            4.0              
complex_fault_mesh_spacing      4.0              
width_of_mfd_bin                0.1              
area_source_discretization      10.0             
ground_motion_correlation_model None             
minimum_intensity               {}               
random_seed                     23               
master_seed                     0                
ses_seed                        42               
=============================== =================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Slowest sources
---------------
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======
grp_id source_id code gidx1 gidx2 num_ruptures calc_time split_time num_sites num_split weight
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======
2      1         S    12    14    1,420        0.0       0.00210    0.0       15        0.0   
1      3         A    8     12    1,815        0.0       1.92977    0.0       121       0.0   
1      1         A    4     8     1,815        0.0       1.36806    0.0       121       0.0   
0      2         A    0     4     1,815        0.0       1.37155    0.0       121       0.0   
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
A    0.0       3     
S    0.0       1     
==== ========= ======

Duplicated sources
------------------
Found 1 source(s) with the same ID and 0 true duplicate(s)
Here is a fake duplicate: 1

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
read_source_models 0.02931 0.02190 0.01383 0.04480 2      
split_filter       0.09339 NaN     0.09339 0.09339 1      
================== ======= ======= ======= ======= =======

Data transfer
-------------
================== ====================================== ========
task               sent                                   received
read_source_models converter=626 B fnames=210 B           5.41 KB 
split_filter       srcs=4.15 KB srcfilter=253 B seed=14 B 87.76 KB
================== ====================================== ========

Slowest operations
------------------
======================== ======== ========= ======
operation                time_sec memory_mb counts
======================== ======== ========= ======
total split_filter       0.09339  2.38672   1     
total read_source_models 0.05863  0.11328   2     
======================== ======== ========= ======