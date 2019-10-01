Event-Based Hazard QA Test, Case 18
===================================

============== ===================
checksum32     3,669,072,072      
date           2019-10-01T06:08:18
engine_version 3.8.0-gite0871b5c35
============== ===================

num_sites = 1, num_levels = 4, num_rlzs = ?

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
SourceReader       0.00915 NaN    0.00915 0.00915 1      
================== ======= ====== ======= ======= =======

Data transfer
-------------
============ ==== ========
task         sent received
SourceReader      28.96 KB
============ ==== ========

Slowest operations
------------------
====================== ======== ========= ======
calc_23118             time_sec memory_mb counts
====================== ======== ========= ======
composite source model 0.01868  0.0       1     
total SourceReader     0.00915  0.0       1     
====================== ======== ========= ======