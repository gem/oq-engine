Test case for the SplitSigma modified GMPE
==========================================

============== ===================
checksum32     4,125,479,680      
date           2019-07-30T15:03:51
engine_version 3.7.0-git3b3dff46da
============== ===================

num_sites = 36, num_levels = 40, num_rlzs = ?

Parameters
----------
=============================== ==================
calculation_mode                'event_based'     
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              5.0               
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                0.2               
area_source_discretization      10.0              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     23                
master_seed                     0                 
ses_seed                        24                
=============================== ==================

Input files
-----------
======================= ========================
Name                    File                    
======================= ========================
gsim_logic_tree         `gmmLt.xml <gmmLt.xml>`_
job_ini                 `job.ini <job.ini>`_    
source_model_logic_tree `ssmLt.xml <ssmLt.xml>`_
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
A    0.0       1     
==== ========= ======

Information about the tasks
---------------------------
================== ======= ====== ======= ======= =======
operation-duration mean    stddev min     max     outputs
read_source_models 0.01078 NaN    0.01078 0.01078 1      
================== ======= ====== ======= ======= =======

Data transfer
-------------
================== =========================== ========
task               sent                        received
read_source_models converter=314 B fnames=95 B 2.31 KB 
================== =========================== ========

Slowest operations
------------------
======================== ======== ========= ======
calc_15473               time_sec memory_mb counts
======================== ======== ========= ======
total read_source_models 0.01078  0.0       1     
======================== ======== ========= ======