Event Based from NonParametric source
=====================================

============== ===================
checksum32     196,267,185        
date           2019-02-18T08:36:14
engine_version 3.4.0-git9883ae17a5
============== ===================

num_sites = 3, num_levels = 7

Parameters
----------
=============================== ==================
calculation_mode                'event_based'     
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 500.0}
investigation_time              50.0              
ses_per_logic_tree_path         2                 
truncation_level                3.0               
rupture_mesh_spacing            5.0               
complex_fault_mesh_spacing      5.0               
width_of_mfd_bin                0.3               
area_source_discretization      20.0              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     23                
master_seed                     0                 
ses_seed                        42                
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
0      1         N    0     420   4            0.0       0.0        0.0       1         0.0   
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
N    0.0       1     
==== ========= ======

Information about the tasks
---------------------------
================== ======= ====== ======= ======= =======
operation-duration mean    stddev min     max     outputs
read_source_models 0.04133 NaN    0.04133 0.04133 1      
only_filter        0.00291 NaN    0.00291 0.00291 1      
================== ======= ====== ======= ======= =======

Data transfer
-------------
================== ======================================== ========
task               sent                                     received
read_source_models converter=313 B fnames=108 B             15.03 KB
only_filter        srcs=14.55 KB srcfilter=253 B dummy=14 B 14.58 KB
================== ======================================== ========

Slowest operations
------------------
======================== ======== ========= ======
operation                time_sec memory_mb counts
======================== ======== ========= ======
total read_source_models 0.04133  0.97266   1     
total only_filter        0.00291  1.86719   1     
======================== ======== ========= ======