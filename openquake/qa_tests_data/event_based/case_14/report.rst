Hazard South Africa
===================

============== ===================
checksum32     3,741,932,100      
date           2019-10-01T06:08:19
engine_version 3.8.0-gite0871b5c35
============== ===================

num_sites = 18, num_levels = 1, num_rlzs = ?

Parameters
----------
=============================== ==================
calculation_mode                'event_based'     
number_of_logic_tree_samples    3                 
maximum_distance                {'default': 100.0}
investigation_time              100.0             
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            5.0               
complex_fault_mesh_spacing      10.0              
width_of_mfd_bin                0.1               
area_source_discretization      20.0              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     113               
master_seed                     0                 
ses_seed                        23                
=============================== ==================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gmmLT.xml <gmmLT.xml>`_                                    
job_ini                 `job.ini <job.ini>`_                                        
site_model              `Site_model_South_Africa.xml <Site_model_South_Africa.xml>`_
source_model_logic_tree `ssmLT.xml <ssmLT.xml>`_                                    
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
A    0.0       10    
==== ========= ======

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
SourceReader       0.17295 0.19384 0.00917 0.50980 10     
================== ======= ======= ======= ======= =======

Data transfer
-------------
============ ============================================== ========
task         sent                                           received
SourceReader apply_unc=40.35 KB ltmodel=3.29 KB fname=990 B 41.22 KB
============ ============================================== ========

Slowest operations
------------------
====================== ======== ========= ======
calc_23123             time_sec memory_mb counts
====================== ======== ========= ======
total SourceReader     1.72948  0.36719   10    
composite source model 0.55055  0.0       1     
====================== ======== ========= ======