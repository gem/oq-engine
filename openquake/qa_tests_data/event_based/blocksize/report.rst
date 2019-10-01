QA test for blocksize independence (hazard)
===========================================

============== ===================
checksum32     2,348,158,649      
date           2019-10-01T06:32:25
engine_version 3.8.0-git66affb82eb
============== ===================

num_sites = 2, num_levels = 4, num_rlzs = ?

Parameters
----------
=============================== ==================
calculation_mode                'event_based'     
number_of_logic_tree_samples    1                 
maximum_distance                {'default': 400.0}
investigation_time              5.0               
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            20.0              
complex_fault_mesh_spacing      20.0              
width_of_mfd_bin                0.5               
area_source_discretization      20.0              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     42                
master_seed                     0                 
ses_seed                        1024              
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
A    0.0       9     
==== ========= ======

Information about the tasks
---------------------------
================== ======= ====== ======= ======= =======
operation-duration mean    stddev min     max     outputs
SourceReader       0.43440 NaN    0.43440 0.43440 1      
================== ======= ====== ======= ======= =======

Data transfer
-------------
============ ==== ========
task         sent received
SourceReader      16.19 KB
============ ==== ========

Slowest operations
------------------
====================== ======== ========= ======
calc_6423              time_sec memory_mb counts
====================== ======== ========= ======
composite source model 0.44408  0.0       1     
total SourceReader     0.43440  0.0       1     
====================== ======== ========= ======