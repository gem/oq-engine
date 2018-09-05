Scenario Risk for Nepal with 20 assets
======================================

============== ===================
checksum32     3,157,733,199      
date           2018-09-05T10:03:39
engine_version 3.2.0-gitb4ef3a4b6c
============== ===================

num_sites = 20, num_levels = 8

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
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
b_1       1.00000 trivial(1)      1/1             
========= ======= =============== ================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)
  0,ChiouYoungs2008(): [0]>

Exposure model
--------------
=============== ========
#assets         20      
#taxonomies     4       
deductibile     relative
insurance_limit relative
=============== ========

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
================== ======= ========= ======= ======= =========
operation-duration mean    stddev    min     max     num_tasks
scenario_risk      0.00560 6.723E-04 0.00455 0.00703 20       
================== ======= ========= ======= ======= =========

Data transfer
-------------
============= ===================================================================== ========
task          sent                                                                  received
scenario_risk riskinputs=150.31 KB riskmodel=47.15 KB monitor=6.04 KB param=2.15 KB 16.02 KB
============= ===================================================================== ========

Slowest operations
------------------
=================== ======== ========= ======
operation           time_sec memory_mb counts
=================== ======== ========= ======
total scenario_risk 0.11209  0.19531   20    
computing risk      0.06780  0.19531   20    
building riskinputs 0.03583  0.05859   1     
getting hazard      0.01920  0.0       40    
saving gmfs         0.01000  0.0       1     
computing gmfs      0.00233  0.0       1     
reading exposure    0.00146  0.0       1     
=================== ======== ========= ======