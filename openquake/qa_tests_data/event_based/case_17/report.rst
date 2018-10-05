Event Based Hazard QA Test, Case 17
===================================

============== ===================
checksum32     2,756,942,605      
date           2018-10-05T03:04:49
engine_version 3.3.0-git48e9a474fd
============== ===================

num_sites = 1, num_levels = 3

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
source                  `source_model_1.xml <source_model_1.xml>`_                  
source                  `source_model_2.xml <source_model_2.xml>`_                  
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Slowest sources
---------------
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======
grp_id source_id code gidx1 gidx2 num_ruptures calc_time split_time num_sites num_split weight
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======
0      1         P    0     1     39           0.0       9.060E-06  0.0       1         0.0   
1      2         P    0     1     7            0.0       3.338E-06  0.0       1         0.0   
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
P    0.0       2     
==== ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ========= ======= ======= =======
operation-duration mean    stddev    min     max     outputs
read_source_models 0.00160 7.317E-05 0.00154 0.00165 2      
split_filter       0.00166 NaN       0.00166 0.00166 1      
================== ======= ========= ======= ======= =======

Data transfer
-------------
================== ====================================================================== ========
task               sent                                                                   received
read_source_models monitor=662 B converter=638 B fnames=372 B                             3.36 KB 
split_filter       srcs=2.1 KB monitor=343 B srcfilter=220 B sample_factor=21 B seed=14 B 2.18 KB 
================== ====================================================================== ========

Slowest operations
------------------
======================== ======== ========= ======
operation                time_sec memory_mb counts
======================== ======== ========= ======
updating source_info     0.00633  0.0       1     
total read_source_models 0.00319  0.0       2     
total split_filter       0.00166  0.0       1     
======================== ======== ========= ======