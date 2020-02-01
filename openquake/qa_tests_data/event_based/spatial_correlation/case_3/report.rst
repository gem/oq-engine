Probabilistic Event-Based QA Test with No Spatial Correlation, case 3
=====================================================================

============== ===================
checksum32     1_038_141_016      
date           2020-01-16T05:30:59
engine_version 3.8.0-git83c45f7244
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
pointsource_distance            None              
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

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      NaN       1            0.0         
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
P    0.0      
==== =========

Information about the tasks
---------------------------
================== ========= ====== ========= ========= =======
operation-duration mean      stddev min       max       outputs
SourceReader       9.608E-04 NaN    9.608E-04 9.608E-04 1      
================== ========= ====== ========= ========= =======

Data transfer
-------------
============ ==== ========
task         sent received
SourceReader      2.08 KB 
============ ==== ========

Slowest operations
------------------
====================== ========= ========= ======
calc_43267             time_sec  memory_mb counts
====================== ========= ========= ======
composite source model 0.01030   0.0       1     
total SourceReader     9.608E-04 0.0       1     
====================== ========= ========= ======