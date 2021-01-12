Scenario Calculation with Simple Fault Rupture
==============================================

============== ====================
checksum32     884_028_645         
date           2020-11-02T09:35:33 
engine_version 3.11.0-git82b78631ac
============== ====================

num_sites = 7, num_levels = 3, num_rlzs = ?

Parameters
----------
=============================== ==========================================
calculation_mode                'scenario'                                
number_of_logic_tree_samples    0                                         
maximum_distance                {'default': [(1.0, 200.0), (10.0, 200.0)]}
investigation_time              None                                      
ses_per_logic_tree_path         1                                         
truncation_level                3.0                                       
rupture_mesh_spacing            2.0                                       
complex_fault_mesh_spacing      2.0                                       
width_of_mfd_bin                None                                      
area_source_discretization      None                                      
pointsource_distance            None                                      
ground_motion_correlation_model 'JB2009'                                  
minimum_intensity               {}                                        
random_seed                     42                                        
master_seed                     0                                         
ses_seed                        42                                        
=============================== ==========================================

Input files
-----------
============= ========================================
Name          File                                    
============= ========================================
job_ini       `job_haz.ini <job_haz.ini>`_            
rupture_model `rupture_model.xml <rupture_model.xml>`_
sites         `sites.csv <sites.csv>`_                
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
calc_47233       time_sec memory_mb counts
================ ======== ========= ======
importing inputs 0.00411  0.0       1     
================ ======== ========= ======