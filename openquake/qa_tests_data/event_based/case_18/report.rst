Event-Based Hazard QA Test, Case 18
===================================

============== ===================
checksum32     98,343,102         
date           2018-10-05T03:04:51
engine_version 3.3.0-git48e9a474fd
============== ===================

num_sites = 1, num_levels = 4

Parameters
----------
=============================== ==================
calculation_mode                'event_based'     
number_of_logic_tree_samples    3                 
maximum_distance                {'default': 200.0}
investigation_time              1.0               
ses_per_logic_tree_path         350               
truncation_level                0.0               
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                0.001             
area_source_discretization      20.0              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     1064              
master_seed                     0                 
ses_seed                        1064              
=============================== ==================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `three_gsim_logic_tree.xml <three_gsim_logic_tree.xml>`_    
job_ini                 `job.ini <job.ini>`_                                        
source                  `source_model.xml <source_model.xml>`_                      
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Slowest sources
---------------
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======
grp_id source_id code gidx1 gidx2 num_ruptures calc_time split_time num_sites num_split weight
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======
0      1         P    0     1     3,000        0.0       3.099E-05  0.0       1         0.0   
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
P    0.0       1     
==== ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ====== ======= ======= =======
operation-duration mean    stddev min     max     outputs
read_source_models 0.00440 NaN    0.00440 0.00440 1      
split_filter       0.02959 NaN    0.02959 0.02959 1      
================== ======= ====== ======= ======= =======

Data transfer
-------------
================== ======================================================================== ========
task               sent                                                                     received
read_source_models monitor=0 B fnames=0 B converter=0 B                                     1.55 KB 
split_filter       srcs=13.01 KB monitor=425 B srcfilter=220 B sample_factor=21 B seed=15 B 13.04 KB
================== ======================================================================== ========

Slowest operations
------------------
======================== ======== ========= ======
operation                time_sec memory_mb counts
======================== ======== ========= ======
updating source_info     0.03697  0.0       1     
total split_filter       0.02959  0.27734   1     
total read_source_models 0.00440  0.0       1     
======================== ======== ========= ======