Scenario Damage
===============

============== ===================
checksum32     2,048,857,716      
date           2018-09-05T10:03:49
engine_version 3.2.0-gitb4ef3a4b6c
============== ===================

num_sites = 7, num_levels = 26

Parameters
----------
=============================== ==================
calculation_mode                'scenario_damage' 
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              None              
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                None              
area_source_discretization      None              
ground_motion_correlation_model 'JB2009'          
minimum_intensity               {}                
random_seed                     42                
master_seed                     0                 
ses_seed                        42                
=============================== ==================

Input files
-----------
==================== ============================================
Name                 File                                        
==================== ============================================
exposure             `exposure_model.xml <exposure_model.xml>`_  
job_ini              `job.ini <job.ini>`_                        
rupture_model        `rupture_model.xml <rupture_model.xml>`_    
sites                `sites.csv <sites.csv>`_                    
structural_fragility `fragility_model.xml <fragility_model.xml>`_
==================== ============================================

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
  0,BooreAtkinson2008(): [0]>

Exposure model
--------------
=============== ========
#assets         1       
#taxonomies     1       
deductibile     absolute
insurance_limit absolute
=============== ========

======== ======= ====== === === ========= ==========
taxonomy mean    stddev min max num_sites num_assets
Wood     1.00000 NaN    1   1   1         1         
======== ======= ====== === === ========= ==========

Information about the tasks
---------------------------
================== ======= ====== ======= ======= =========
operation-duration mean    stddev min     max     num_tasks
scenario_damage    0.00408 NaN    0.00408 0.00408 1        
================== ======= ====== ======= ======= =========

Data transfer
-------------
=============== ================================================== ========
task            sent                                               received
scenario_damage riskmodel=0 B riskinputs=0 B param=0 B monitor=0 B 5.27 KB 
=============== ================================================== ========

Slowest operations
------------------
===================== ========= ========= ======
operation             time_sec  memory_mb counts
===================== ========= ========= ======
total scenario_damage 0.00408   0.0       1     
computing risk        0.00236   0.0       1     
building riskinputs   0.00189   0.0       1     
saving gmfs           0.00157   0.0       1     
computing gmfs        0.00152   0.0       1     
reading exposure      5.209E-04 0.0       1     
getting hazard        4.966E-04 0.0       2     
===================== ========= ========= ======