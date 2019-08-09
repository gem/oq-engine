Hazard Japan (HERP model 2014) reduced
======================================

============== ===================
checksum32     2,896,463,652      
date           2019-07-30T15:03:50
engine_version 3.7.0-git3b3dff46da
============== ===================

num_sites = 5, num_levels = 1, num_rlzs = ?

Parameters
----------
=============================== ==================
calculation_mode                'event_based'     
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 300.0}
investigation_time              50.0              
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            5.0               
complex_fault_mesh_spacing      10.0              
width_of_mfd_bin                0.1               
area_source_discretization      10.0              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     113               
master_seed                     0                 
ses_seed                        42                
=============================== ==================

Input files
-----------
======================= ==============================================
Name                    File                                          
======================= ==============================================
gsim_logic_tree         `gmmLT_sa.xml <gmmLT_sa.xml>`_                
job_ini                 `job.ini <job.ini>`_                          
site_model              `Site_model_Japan.xml <Site_model_Japan.xml>`_
source_model_logic_tree `ssmLT.xml <ssmLT.xml>`_                      
======================= ==============================================

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ====== =====
source_id grp_id code num_ruptures calc_time num_sites weight speed
========= ====== ==== ============ ========= ========= ====== =====
========= ====== ==== ============ ========= ========= ====== =====

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
N    0.0       1     
P    0.0       1     
==== ========= ======

Information about the tasks
---------------------------
================== ======= ====== ======= ======= =======
operation-duration mean    stddev min     max     outputs
read_source_models 0.00154 NaN    0.00154 0.00154 1      
================== ======= ====== ======= ======= =======

Data transfer
-------------
================== ============================ ========
task               sent                         received
read_source_models converter=314 B fnames=112 B 6.62 KB 
================== ============================ ========

Slowest operations
------------------
======================== ======== ========= ======
calc_15470               time_sec memory_mb counts
======================== ======== ========= ======
total read_source_models 0.00154  0.0       1     
======================== ======== ========= ======