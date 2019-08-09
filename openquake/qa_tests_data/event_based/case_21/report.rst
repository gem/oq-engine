Event Based PSHA
================

============== ===================
checksum32     269,549,222        
date           2019-07-30T15:03:49
engine_version 3.7.0-git3b3dff46da
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
==== ========= ======

Information about the tasks
---------------------------
================== ======= ====== ======= ======= =======
operation-duration mean    stddev min     max     outputs
read_source_models 0.02625 NaN    0.02625 0.02625 1      
================== ======= ====== ======= ======= =======

Data transfer
-------------
================== =========================== ========
task               sent                        received
read_source_models converter=314 B fnames=95 B 23.87 KB
================== =========================== ========

Slowest operations
------------------
======================== ======== ========= ======
calc_15465               time_sec memory_mb counts
======================== ======== ========= ======
total read_source_models 0.02625  0.0       1     
======================== ======== ========= ======