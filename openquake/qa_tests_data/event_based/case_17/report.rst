Event Based Hazard QA Test, Case 17
===================================

============== ===================
checksum32     2,756,942,605      
date           2019-03-19T10:04:04
engine_version 3.5.0-gitad6b69ea66
============== ===================

num_sites = 1, num_levels = 3, num_rlzs = ?

Parameters
----------
=============================== ==================
calculation_mode                'event_based'     
number_of_logic_tree_samples    5                 
maximum_distance                {'default': 200.0}
investigation_time              1.0               
ses_per_logic_tree_path         3                 
truncation_level                2.0               
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                1.0               
area_source_discretization      20.0              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     106               
master_seed                     0                 
ses_seed                        106               
=============================== ==================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gsim_logic_tree.xml <gsim_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Slowest sources
---------------
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======
grp_id source_id code gidx1 gidx2 num_ruptures calc_time split_time num_sites num_split weight
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======
1      2         P    1     2     7            0.0       0.0        0.0       1         0.0   
0      1         P    0     1     39           0.0       0.0        0.0       1         0.0   
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
P    0.0       2     
==== ========= ======

Information about the tasks
---------------------------
================== ======= ========= ======= ======= =======
operation-duration mean    stddev    min     max     outputs
read_source_models 0.00129 4.400E-05 0.00126 0.00132 2      
only_filter        0.00260 NaN       0.00260 0.00260 1      
================== ======= ========= ======= ======= =======

Data transfer
-------------
================== ======================================= ========
task               sent                                    received
read_source_models converter=626 B fnames=222 B            3.4 KB  
only_filter        srcs=1.79 KB srcfilter=253 B dummy=14 B 1.92 KB 
================== ======================================= ========

Slowest operations
------------------
======================== ======== ========= ======
operation                time_sec memory_mb counts
======================== ======== ========= ======
total only_filter        0.00260  1.44531   1     
total read_source_models 0.00258  0.06641   2     
======================== ======== ========= ======