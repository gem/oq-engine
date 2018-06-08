Scenario Risk with site model
=============================

============== ===================
checksum32     1,603,095,237      
date           2018-06-05T06:40:10
engine_version 3.2.0-git65c4735   
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
#assets         11      
#taxonomies     4       
deductibile     absolute
insurance_limit absolute
=============== ========

============ ======= ====== === === ========= ==========
taxonomy     mean    stddev min max num_sites num_assets
EMCA_PRIM_2L 1.00000 0.0    1   1   4         4         
EMCA_PRIM_4L 1.00000 NaN    1   1   1         1         
concrete_spl 1.00000 0.0    1   1   3         3         
steel_spl    1.00000 0.0    1   1   3         3         
*ALL*        1.00000 0.0    1   1   11        11        
============ ======= ====== === === ========= ==========

Slowest operations
------------------
======================= ========= ========= ======
operation               time_sec  memory_mb counts
======================= ========= ========= ======
ScenarioCalculator.run  0.27205   0.00391   1     
reading site collection 0.05950   0.0       1     
building riskinputs     0.03101   0.0       1     
saving gmfs             0.00814   0.0       1     
computing gmfs          0.00479   0.0       1     
reading exposure        0.00188   0.0       1     
building epsilons       6.657E-04 0.0       1     
======================= ========= ========= ======