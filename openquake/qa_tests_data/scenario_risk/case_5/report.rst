Scenario Risk with site model
=============================

============== ===================
checksum32     1,603,095,237      
date           2018-05-15T04:14:26
engine_version 3.1.0-git0acbc11   
============== ===================

num_sites = 11, num_levels = 106

Parameters
----------
=============================== ==================
calculation_mode                'scenario_risk'   
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
avg_losses                      True              
=============================== ==================

Input files
-----------
======================== ==========================================================================
Name                     File                                                                      
======================== ==========================================================================
exposure                 `exposure_roads_bridges.xml <exposure_roads_bridges.xml>`_                
job_ini                  `job.ini <job.ini>`_                                                      
rupture_model            `fault_rupture.xml <fault_rupture.xml>`_                                  
site_model               `VS30_grid_0.05_towns.xml <VS30_grid_0.05_towns.xml>`_                    
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
  0,AkkarEtAlRjb2014(): [0]>

Exposure model
--------------
=============== ========
#assets         18      
#taxonomies     4       
deductibile     absolute
insurance_limit absolute
=============== ========

============ ======= ======= === === ========= ==========
taxonomy     mean    stddev  min max num_sites num_assets
EMCA_PRIM_2L 1.11111 0.33333 1   2   9         10        
EMCA_PRIM_4L 1.00000 NaN     1   1   1         1         
concrete_spl 1.00000 0.0     1   1   4         4         
steel_spl    1.00000 0.0     1   1   3         3         
*ALL*        1.05882 0.24254 1   2   17        18        
============ ======= ======= === === ========= ==========

Slowest operations
------------------
======================= ======== ========= ======
operation               time_sec memory_mb counts
======================= ======== ========= ======
building riskinputs     0.06543  0.0       1     
reading site collection 0.02734  0.0       1     
saving gmfs             0.01174  0.0       1     
computing gmfs          0.00644  0.0       1     
reading exposure        0.00206  0.0       1     
building epsilons       0.00135  0.0       1     
======================= ======== ========= ======