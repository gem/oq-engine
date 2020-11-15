oq-test03, depth=15km
=====================

============== ====================
checksum32     3_161_979_157       
date           2020-11-02T09:35:48 
engine_version 3.11.0-git82b78631ac
============== ====================

num_sites = 1, num_levels = 2, num_rlzs = ?

Parameters
----------
=============================== ======================================
calculation_mode                'scenario_damage'                     
number_of_logic_tree_samples    0                                     
maximum_distance                {'default': [(1.0, 300), (10.0, 300)]}
investigation_time              None                                  
ses_per_logic_tree_path         1                                     
truncation_level                3.0                                   
rupture_mesh_spacing            0.1                                   
complex_fault_mesh_spacing      0.1                                   
width_of_mfd_bin                None                                  
area_source_discretization      None                                  
pointsource_distance            None                                  
ground_motion_correlation_model None                                  
minimum_intensity               {}                                    
random_seed                     3                                     
master_seed                     0                                     
ses_seed                        42                                    
=============================== ======================================

Input files
-----------
==================== ============================================================================
Name                 File                                                                        
==================== ============================================================================
exposure             `exposure_model_Antioquia_test03.xml <exposure_model_Antioquia_test03.xml>`_
job_ini              `job_h.ini <job_h.ini>`_                                                    
rupture_model        `rupture_Romeral_15km.xml <rupture_Romeral_15km.xml>`_                      
structural_fragility `fragility_model_test03.xml <fragility_model_test03.xml>`_                  
==================== ============================================================================

Exposure model
--------------
=========== =
#assets     5
#taxonomies 5
=========== =

============== ========== ======= ====== === === =========
taxonomy       num_assets mean    stddev min max num_sites
MUR/LWAL/HEX:1 1          1.00000 nan    1   1   1        
MUR/LWAL/HEX:2 1          1.00000 nan    1   1   1        
MUR/LWAL/HEX:3 1          1.00000 nan    1   1   1        
MUR/LWAL/HEX:4 1          1.00000 nan    1   1   1        
MUR/LWAL/HEX:5 1          1.00000 nan    1   1   1        
*ALL*          1          5.00000 nan    5   5   5        
============== ========== ======= ====== === === =========

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
calc_47248       time_sec  memory_mb counts
================ ========= ========= ======
importing inputs 0.03241   0.0       1     
reading exposure 5.300E-04 0.0       1     
================ ========= ========= ======