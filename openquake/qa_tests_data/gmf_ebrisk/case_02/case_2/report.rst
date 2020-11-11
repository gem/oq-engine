Event Based Risk from GMF
=========================

============== ====================
checksum32     4_053_279_609       
date           2020-11-02T09:35:30 
engine_version 3.11.0-git82b78631ac
============== ====================

num_sites = 3, num_levels = 2, num_rlzs = 1

Parameters
----------
=============================== ==================
calculation_mode                'event_based_risk'
number_of_logic_tree_samples    0                 
maximum_distance                None              
investigation_time              1.0               
ses_per_logic_tree_path         1                 
truncation_level                None              
rupture_mesh_spacing            5.0               
complex_fault_mesh_spacing      5.0               
width_of_mfd_bin                None              
area_source_discretization      None              
pointsource_distance            None              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     42                
master_seed                     0                 
ses_seed                        42                
avg_losses                      True              
=============================== ==================

Input files
-----------
======================== ================================================
Name                     File                                            
======================== ================================================
exposure                 `exposure_model_2.xml <exposure_model_2.xml>`_  
gmfs                     `gmfs_3_2IM.csv <gmfs_3_2IM.csv>`_              
job_ini                  `job.ini <job.ini>`_                            
sites                    `sitemesh.csv <sitemesh.csv>`_                  
structural_vulnerability `vulnerability_2IM.xml <vulnerability_2IM.xml>`_
======================== ================================================

Composite source model
----------------------
====== ============ ====
grp_id gsim         rlzs
====== ============ ====
0      '[FromFile]' [0] 
====== ============ ====

Estimated data transfer for the avglosses
-----------------------------------------
3 asset(s) x 1 realization(s) x 1 loss type(s) losses x 8 bytes x 20 tasks = 480 B

Exposure model
--------------
=========== =
#assets     3
#taxonomies 2
=========== =

======== ========== ======= ====== === === =========
taxonomy num_assets mean    stddev min max num_sites
RM       2          1.00000 0%     1   1   2        
RC       1          1.00000 nan    1   1   1        
*ALL*    3          1.00000 0%     1   1   3        
======== ========== ======= ====== === === =========

Information about the tasks
---------------------------
Not available

Data transfer
-------------
==== ==== ========
task sent received
==== ==== ========

Slowest operations
------------------
================ ========= ========= ======
calc_47209       time_sec  memory_mb counts
================ ========= ========= ======
importing inputs 0.01916   0.25000   1     
reading exposure 8.466E-04 0.0       1     
================ ========= ========= ======