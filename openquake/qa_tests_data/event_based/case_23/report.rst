Example EB Hazard. Infer region from exposure model
===================================================

============== ===================
checksum32     1_469_780_630      
date           2020-01-16T05:31:02
engine_version 3.8.0-git83c45f7244
============== ===================

num_sites = 93, num_levels = 0, num_rlzs = ?

Parameters
----------
=============================== ==================
calculation_mode                'event_based'     
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              1.0               
ses_per_logic_tree_path         5                 
truncation_level                3.0               
rupture_mesh_spacing            5.0               
complex_fault_mesh_spacing      5.0               
width_of_mfd_bin                0.5               
area_source_discretization      10.0              
pointsource_distance            None              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     42                
master_seed                     0                 
ses_seed                        42                
=============================== ==================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
exposure                `exposure_model.xml <exposure_model.xml>`_                  
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
site_model              `site_model.csv <site_model.csv>`_                          
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      NaN       23_314       0.0         
====== ========= ============ ============

Exposure model
--------------
=========== ==
#assets     96
#taxonomies 5 
=========== ==

========================== ======= ======= === === ========= ==========
taxonomy                   mean    stddev  min max num_sites num_assets
Wood                       1.00000 0.0     1   1   23        23        
Adobe                      1.00000 0.0     1   1   29        29        
Stone-Masonry              1.00000 0.0     1   1   16        16        
Unreinforced-Brick-Masonry 1.00000 0.0     1   1   27        27        
Concrete                   1.00000 NaN     1   1   1         1         
*ALL*                      0.03601 0.19229 0   2   2_666     96        
========================== ======= ======= === === ========= ==========

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
A    0.0      
==== =========

Information about the tasks
---------------------------
================== ======= ====== ======= ======= =======
operation-duration mean    stddev min     max     outputs
SourceReader       0.94569 NaN    0.94569 0.94569 1      
================== ======= ====== ======= ======= =======

Data transfer
-------------
============ ==== ========
task         sent received
SourceReader      23.61 KB
============ ==== ========

Slowest operations
------------------
====================== ======== ========= ======
calc_43284             time_sec memory_mb counts
====================== ======== ========= ======
composite source model 0.95940  0.0       1     
total SourceReader     0.94569  0.0       1     
reading exposure       0.01314  0.0       1     
====================== ======== ========= ======