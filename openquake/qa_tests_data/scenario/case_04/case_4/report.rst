Scenario QA Test, Case 1
========================

============== ====================
checksum32     4_231_056_651       
date           2020-11-02T09:35:30 
engine_version 3.11.0-git82b78631ac
============== ====================

num_sites = 3, num_levels = 1, num_rlzs = ?

Parameters
----------
=============================== ======================================
calculation_mode                'scenario'                            
number_of_logic_tree_samples    0                                     
maximum_distance                {'default': [(1.0, 200), (10.0, 200)]}
investigation_time              None                                  
ses_per_logic_tree_path         1                                     
truncation_level                1.0                                   
rupture_mesh_spacing            1.0                                   
complex_fault_mesh_spacing      1.0                                   
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
============= ========================================
Name          File                                    
============= ========================================
job_ini       `job.ini <job.ini>`_                    
rupture_model `rupture_model.xml <rupture_model.xml>`_
site_model    `site_model.xml <site_model.xml>`_      
============= ========================================

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
calc_47212       time_sec memory_mb counts
================ ======== ========= ======
importing inputs 0.00630  0.0       1     
================ ======== ========= ======