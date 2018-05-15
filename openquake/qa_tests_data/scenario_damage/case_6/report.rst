oq-test03, depth=15km
=====================

============== ===================
checksum32     3,074,586,051      
date           2018-05-15T04:12:41
engine_version 3.1.0-git0acbc11   
============== ===================

num_sites = 1, num_levels = 40

Parameters
----------
=============================== ==================
calculation_mode                'scenario_damage' 
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 300.0}
investigation_time              None              
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            0.1               
complex_fault_mesh_spacing      0.1               
width_of_mfd_bin                None              
area_source_discretization      None              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     3                 
master_seed                     0                 
ses_seed                        42                
=============================== ==================

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
  0,SadighEtAl1997(): [0]>

Exposure model
--------------
=============== ========
#assets         5       
#taxonomies     5       
deductibile     absolute
insurance_limit absolute
=============== ========

============== ======= ====== === === ========= ==========
taxonomy       mean    stddev min max num_sites num_assets
MUR/LWAL/HEX:1 1.00000 NaN    1   1   1         1         
MUR/LWAL/HEX:2 1.00000 NaN    1   1   1         1         
MUR/LWAL/HEX:3 1.00000 NaN    1   1   1         1         
MUR/LWAL/HEX:4 1.00000 NaN    1   1   1         1         
MUR/LWAL/HEX:5 1.00000 NaN    1   1   1         1         
*ALL*          5.00000 NaN    5   5   1         5         
============== ======= ====== === === ========= ==========

Slowest operations
------------------
======================= ========= ========= ======
operation               time_sec  memory_mb counts
======================= ========= ========= ======
reading site collection 0.00150   0.0       1     
reading exposure        4.508E-04 0.0       1     
======================= ========= ========= ======