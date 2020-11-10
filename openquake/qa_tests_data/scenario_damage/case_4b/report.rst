scenario hazard
===============

============== ====================
checksum32     366_357_960         
date           2020-11-02T09:35:49 
engine_version 3.11.0-git82b78631ac
============== ====================

num_sites = 7, num_levels = 1, num_rlzs = ?

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
=============== ============================================
Name            File                                        
=============== ============================================
exposure        `exposure_model.xml <exposure_model.xml>`_  
gsim_logic_tree `gsim_logic_tree.xml <gsim_logic_tree.xml>`_
job_ini         `job_haz.ini <job_haz.ini>`_                
rupture_model   `rupture_model.xml <rupture_model.xml>`_    
=============== ============================================

Exposure model
--------------
=========== =
#assets     7
#taxonomies 3
=========== =

======== ========== ======= ====== === === =========
taxonomy num_assets mean    stddev min max num_sites
tax1     4          1.00000 0%     1   1   4        
tax2     2          1.00000 0%     1   1   2        
tax3     1          1.00000 nan    1   1   1        
*ALL*    7          1.00000 0%     1   1   7        
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
calc_47255       time_sec  memory_mb counts
================ ========= ========= ======
importing inputs 0.01400   0.0       1     
reading exposure 6.678E-04 0.0       1     
================ ========= ========= ======