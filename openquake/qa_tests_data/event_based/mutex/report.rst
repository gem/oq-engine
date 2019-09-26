Event Based QA Test, Case 1
===========================

============== ===================
checksum32     3,529,984,501      
date           2019-09-24T15:21:05
engine_version 3.7.0-git749bb363b3
============== ===================

num_sites = 1, num_levels = 46, num_rlzs = ?

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
========= ====== ==== ============ ========= ========= ============ =====
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures speed
========= ====== ==== ============ ========= ========= ============ =====
========= ====== ==== ============ ========= ========= ============ =====

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
N    0.0       10    
==== ========= ======

Information about the tasks
---------------------------
================== ======= ====== ======= ======= =======
operation-duration mean    stddev min     max     outputs
read_source_models 0.17650 NaN    0.17650 0.17650 1      
================== ======= ====== ======= ======= =======

Data transfer
-------------
================== ============================ =========
task               sent                         received 
read_source_models converter=314 B fnames=107 B 756.12 KB
================== ============================ =========

Slowest operations
------------------
======================== ======== ========= ======
calc_1790                time_sec memory_mb counts
======================== ======== ========= ======
total read_source_models 0.17650  3.54688   1     
======================== ======== ========= ======