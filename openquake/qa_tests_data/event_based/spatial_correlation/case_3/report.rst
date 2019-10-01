Probabilistic Event-Based QA Test with No Spatial Correlation, case 3
=====================================================================

============== ===================
checksum32     1,038,141,016      
date           2019-10-01T06:08:19
engine_version 3.8.0-gite0871b5c35
============== ===================

num_sites = 2, num_levels = 1, num_rlzs = ?

Parameters
----------
=============================== ==================
calculation_mode                'event_based'     
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              50.0              
ses_per_logic_tree_path         300               
truncation_level                None              
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                0.1               
area_source_discretization      20.0              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     42                
master_seed                     0                 
ses_seed                        123456789         
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
========= ====== ==== ============ ========= ========= ============ =====
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures speed
========= ====== ==== ============ ========= ========= ============ =====
========= ====== ==== ============ ========= ========= ============ =====

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
P    0.0       1     
==== ========= ======

Information about the tasks
---------------------------
================== ======= ====== ======= ======= =======
operation-duration mean    stddev min     max     outputs
SourceReader       0.00199 NaN    0.00199 0.00199 1      
================== ======= ====== ======= ======= =======

Data transfer
-------------
============ ==== ========
task         sent received
SourceReader      2.58 KB 
============ ==== ========

Slowest operations
------------------
====================== ======== ========= ======
calc_23120             time_sec memory_mb counts
====================== ======== ========= ======
composite source model 0.01461  0.0       1     
total SourceReader     0.00199  0.0       1     
====================== ======== ========= ======