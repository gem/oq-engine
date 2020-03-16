Scenario QA Test with Spatial Correlation - Case 2
==================================================

============== ===================
checksum32     2_135_006_889      
date           2020-03-13T11:20:15
engine_version 3.9.0-gitfb3ef3a732
============== ===================

num_sites = 2, num_levels = 1, num_rlzs = 1

Parameters
----------
=============================== ==================
calculation_mode                'scenario'        
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              None              
ses_per_logic_tree_path         1                 
truncation_level                None              
rupture_mesh_spacing            1.0               
complex_fault_mesh_spacing      1.0               
width_of_mfd_bin                None              
area_source_discretization      None              
pointsource_distance            {'default': {}}   
ground_motion_correlation_model 'JB2009'          
minimum_intensity               {}                
random_seed                     3                 
master_seed                     0                 
ses_seed                        42                
=============================== ==================

Input files
-----------
============= ========================================
Name          File                                    
============= ========================================
job_ini       `job.ini <job.ini>`_                    
rupture_model `rupture_model.xml <rupture_model.xml>`_
============= ========================================

Composite source model
----------------------
========= ======= ================
smlt_path weight  num_realizations
========= ======= ================
b_1       1.00000 1               
========= ======= ================

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
========== ======== ========= ======
calc_66862 time_sec memory_mb counts
========== ======== ========= ======
========== ======== ========= ======