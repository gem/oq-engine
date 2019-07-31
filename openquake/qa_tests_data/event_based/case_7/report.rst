Event-based PSHA with logic tree sampling
=========================================

============== ===================
checksum32     1,264,506,295      
date           2019-07-30T15:03:51
engine_version 3.7.0-git3b3dff46da
============== ===================

num_sites = 3, num_levels = 7, num_rlzs = ?

Parameters
----------
=============================== ==================
calculation_mode                'event_based'     
number_of_logic_tree_samples    100               
maximum_distance                {'default': 200.0}
investigation_time              50.0              
ses_per_logic_tree_path         20                
truncation_level                3.0               
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                0.2               
area_source_discretization      20.0              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     23                
master_seed                     0                 
ses_seed                        23                
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
========= ====== ==== ============ ========= ========= ====== =====
source_id grp_id code num_ruptures calc_time num_sites weight speed
========= ====== ==== ============ ========= ========= ====== =====
========= ====== ==== ============ ========= ========= ====== =====

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
A    0.0       2     
==== ========= ======

Information about the tasks
---------------------------
================== ======= ========= ======= ======= =======
operation-duration mean    stddev    min     max     outputs
read_source_models 0.06129 5.361E-05 0.06125 0.06132 2      
================== ======= ========= ======= ======= =======

Data transfer
-------------
================== ============================ ========
task               sent                         received
read_source_models converter=628 B fnames=204 B 8.41 KB 
================== ============================ ========

Slowest operations
------------------
======================== ======== ========= ======
calc_15475               time_sec memory_mb counts
======================== ======== ========= ======
total read_source_models 0.12257  0.0       2     
======================== ======== ========= ======