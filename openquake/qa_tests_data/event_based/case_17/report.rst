Event Based Hazard QA Test, Case 17
===================================

============== ===================
checksum32     1_693_427_193      
date           2020-01-16T05:31:00
engine_version 3.8.0-git83c45f7244
============== ===================

num_sites = 1, num_levels = 3, num_rlzs = ?

Parameters
----------
=============================== ==================
calculation_mode                'event_based'     
number_of_logic_tree_samples    5                 
maximum_distance                {'default': 200.0}
investigation_time              1.0               
ses_per_logic_tree_path         3                 
truncation_level                2.0               
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                1.0               
area_source_discretization      20.0              
pointsource_distance            None              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     106               
master_seed                     0                 
ses_seed                        106               
=============================== ==================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gsim_logic_tree.xml <gsim_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      NaN       39           0.0         
1      NaN       7            0.0         
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
================== ======= ========= ======= ======= =======
operation-duration mean    stddev    min     max     outputs
SourceReader       0.00166 7.489E-04 0.00113 0.00219 2      
================== ======= ========= ======= ======= =======

Data transfer
-------------
============ =========================================== ========
task         sent                                        received
SourceReader apply_unc=2.29 KB ltmodel=378 B fname=216 B 4.55 KB 
============ =========================================== ========

Slowest operations
------------------
====================== ======== ========= ======
calc_43271             time_sec memory_mb counts
====================== ======== ========= ======
composite source model 0.02533  0.0       1     
total SourceReader     0.00332  0.0       2     
====================== ======== ========= ======