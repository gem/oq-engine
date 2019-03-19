Event Based PSHA
================

============== ===================
checksum32     269,549,222        
date           2019-03-19T10:03:56
engine_version 3.5.0-gitad6b69ea66
============== ===================

num_sites = 1, num_levels = 3, num_rlzs = ?

Parameters
----------
=============================== ==================
calculation_mode                'event_based'     
number_of_logic_tree_samples    1000              
maximum_distance                {'default': 200.0}
investigation_time              1.0               
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                0.1               
area_source_discretization      5.0               
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     42                
master_seed                     0                 
ses_seed                        24                
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
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======
grp_id source_id code gidx1 gidx2 num_ruptures calc_time split_time num_sites num_split weight
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======
0      1_1       N    0     913   2            0.0       0.0        0.0       1         0.0   
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
read_source_models 0.01465 NaN    0.01465 0.01465 1      
only_filter        0.00279 NaN    0.00279 0.00279 1      
================== ======= ====== ======= ======= =======

Data transfer
-------------
================== ======================================== ========
task               sent                                     received
read_source_models converter=313 B fnames=102 B             23.88 KB
only_filter        srcs=23.69 KB srcfilter=253 B dummy=14 B 23.42 KB
================== ======================================== ========

Slowest operations
------------------
======================== ======== ========= ======
operation                time_sec memory_mb counts
======================== ======== ========= ======
total read_source_models 0.01465  0.21875   1     
total only_filter        0.00279  1.44922   1     
======================== ======== ========= ======