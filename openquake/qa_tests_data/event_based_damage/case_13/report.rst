Event Based Damage
==================

============== ====================
checksum32     3_590_982_611       
date           2021-04-15T10:42:28 
engine_version 3.12.0-git61ac21bcb2
============== ====================

num_sites = 3, num_levels = 1, num_rlzs = 1

Parameters
----------
=============================== ==========================================
calculation_mode                'event_based_damage'                      
number_of_logic_tree_samples    0                                         
maximum_distance                {'default': [[1.0, 100.0], [10.0, 100.0]]}
investigation_time              50.0                                      
ses_per_logic_tree_path         20                                        
truncation_level                None                                      
rupture_mesh_spacing            5.0                                       
complex_fault_mesh_spacing      5.0                                       
width_of_mfd_bin                None                                      
area_source_discretization      None                                      
pointsource_distance            None                                      
ground_motion_correlation_model None                                      
minimum_intensity               {'PGA': 1e-10}                            
random_seed                     42                                        
master_seed                     123456789                                 
ses_seed                        42                                        
=============================== ==========================================

Input files
-----------
==================== ================================
Name                 File                            
==================== ================================
exposure             `exposure1.xml <exposure1.xml>`_
gmfs                 `gmfs.csv <gmfs.csv>`_          
job_ini              `job.ini <job.ini>`_            
sites                `sites.csv <sites.csv>`_        
structural_fragility `fragility.xml <fragility.xml>`_
==================== ================================

Composite source model
----------------------
====== ============ ====
grp_id gsim         rlzs
====== ============ ====
0      '[FromFile]' [0] 
====== ============ ====

Exposure model
--------------
=========== =
#assets     4
#taxonomies 3
=========== =

======== ========== ======= ====== === === =========
taxonomy num_assets mean    stddev min max num_sites
RM       2          1.00000 0%     1   1   2        
W        1          1.00000 nan    1   1   1        
RC       1          1.00000 nan    1   1   1        
*ALL*    3          1.33333 35%    1   2   4        
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
================ ======== ========= ======
calc_541         time_sec memory_mb counts
================ ======== ========= ======
importing inputs 0.03461  2.37500   1     
reading exposure 0.00491  0.0       1     
================ ======== ========= ======