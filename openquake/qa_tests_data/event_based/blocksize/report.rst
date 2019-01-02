QA test for blocksize independence (hazard)
===========================================

============== ===================
checksum32     2,348,158,649      
date           2018-12-13T12:57:23
engine_version 3.3.0-git68d7d11268
============== ===================

num_sites = 2, num_levels = 4

Parameters
----------
=============================== ==================
calculation_mode                'event_based'     
number_of_logic_tree_samples    1                 
maximum_distance                {'default': 400.0}
investigation_time              5.0               
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            20.0              
complex_fault_mesh_spacing      20.0              
width_of_mfd_bin                0.5               
area_source_discretization      20.0              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     42                
master_seed                     0                 
ses_seed                        1024              
=============================== ==================

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
0      1         A    0     4     1,752        0.0       26         0.0       292       0.0   
0      2         A    4     8     582          0.0       2.71909    0.0       97        0.0   
0      3         A    8     12    440          0.0       1.36021    0.0       57        0.0   
0      4         A    12    16    267          0.0       0.0        0.0       0         0.0   
0      5         A    16    20    518          0.0       0.0        0.0       0         0.0   
0      6         A    20    24    316          0.0       0.0        0.0       0         0.0   
0      7         A    24    28    1,028        0.0       0.0        0.0       0         0.0   
0      8         A    28    32    447          0.0       0.0        0.0       0         0.0   
0      9         A    32    36    222          0.0       0.05049    0.0       2         0.0   
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
A    0.0       9     
==== ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ====== ======= ======= =======
operation-duration mean    stddev min     max     outputs
read_source_models 0.49892 NaN    0.49892 0.49892 1      
split_filter       0.59246 NaN    0.59246 0.59246 1      
================== ======= ====== ======= ======= =======

Data transfer
-------------
================== ====================================== ========
task               sent                                   received
read_source_models converter=388 B fnames=111 B           9.21 KB 
split_filter       srcs=8.92 KB srcfilter=253 B seed=14 B 136.3 KB
================== ====================================== ========

Slowest operations
------------------
======================== ======== ========= ======
operation                time_sec memory_mb counts
======================== ======== ========= ======
total split_filter       0.59246  1.42578   1     
total read_source_models 0.49892  0.0       1     
======================== ======== ========= ======