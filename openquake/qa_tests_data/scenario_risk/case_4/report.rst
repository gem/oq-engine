Scenario Risk for Nepal with 20 assets
======================================

============== ===================
checksum32     2_743_600_684      
date           2020-03-13T11:20:17
engine_version 3.9.0-gitfb3ef3a732
============== ===================

num_sites = 20, num_levels = 1, num_rlzs = 1

Parameters
----------
=============================== ==================
calculation_mode                'scenario_risk'   
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 500.0}
investigation_time              None              
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            15.0              
complex_fault_mesh_spacing      15.0              
width_of_mfd_bin                None              
area_source_discretization      None              
pointsource_distance            {'default': {}}   
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     42                
master_seed                     0                 
ses_seed                        42                
avg_losses                      True              
=============================== ==================

Input files
-----------
======================== ==========================================================================
Name                     File                                                                      
======================== ==========================================================================
exposure                 `exposure_model.xml <exposure_model.xml>`_                                
job_ini                  `job.ini <job.ini>`_                                                      
rupture_model            `fault_rupture.xml <fault_rupture.xml>`_                                  
structural_vulnerability `structural_vulnerability_model.xml <structural_vulnerability_model.xml>`_
======================== ==========================================================================

Composite source model
----------------------
========= ======= ================
smlt_path weight  num_realizations
========= ======= ================
b_1       1.00000 1               
========= ======= ================

Exposure model
--------------
=========== ==
#assets     20
#taxonomies 4 
=========== ==

========================== ======= ====== === === ========= ==========
taxonomy                   mean    stddev min max num_sites num_assets
Wood                       1.00000 0.0    1   1   8         8         
Adobe                      1.00000 0.0    1   1   3         3         
Stone-Masonry              1.00000 0.0    1   1   4         4         
Unreinforced-Brick-Masonry 1.00000 0.0    1   1   5         5         
*ALL*                      1.00000 0.0    1   1   20        20        
========================== ======= ====== === === ========= ==========

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
====================== ========= ========= ======
calc_66877             time_sec  memory_mb counts
====================== ========= ========= ======
ScenarioCalculator.run 0.06360   0.0       1     
saving gmfs            0.00986   0.0       1     
building riskinputs    0.00381   0.0       1     
computing gmfs         0.00160   0.0       1     
reading exposure       7.985E-04 0.0       1     
====================== ========= ========= ======