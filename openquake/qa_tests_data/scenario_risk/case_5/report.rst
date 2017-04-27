Scenario Risk with site model
=============================

=============================================== ========================
tstation.gem.lan:/mnt/ssd/oqdata/calc_7643.hdf5 Wed Apr 26 15:56:32 2017
engine_version                                  2.4.0-git9336bd0        
hazardlib_version                               0.24.0-gita895d4c       
=============================================== ========================

num_sites = 11, sitecol = 1.74 KB

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
random_seed                     42                
master_seed                     0                 
avg_losses                      False             
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

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)
  0,AkkarEtAlRjb2014(): ['<0,b_1~b1,w=1.0>']>

Informational data
------------------
================ ================
hostname         tstation.gem.lan
require_epsilons 1 B             
================ ================

Exposure model
--------------
=============== ========
#assets         18      
#taxonomies     4       
deductibile     absolute
insurance_limit absolute
=============== ========

============ ===== ====== === === ========= ==========
taxonomy     mean  stddev min max num_sites num_assets
EMCA_PRIM_2L 1.111 0.333  1   2   9         10        
EMCA_PRIM_4L 1.000 NaN    1   1   1         1         
concrete_spl 1.000 0.0    1   1   4         4         
steel_spl    1.000 0.0    1   1   3         3         
*ALL*        1.059 0.243  1   2   17        18        
============ ===== ====== === === ========= ==========

Slowest operations
------------------
======================== ========= ========= ======
operation                time_sec  memory_mb counts
======================== ========= ========= ======
filtering sites          0.040     0.0       1     
building site collection 0.024     0.0       1     
computing gmfs           0.010     0.0       1     
reading exposure         0.002     0.0       1     
saving gmfs              0.001     0.0       1     
building riskinputs      6.132E-04 0.0       1     
building epsilons        4.551E-04 0.0       1     
reading site collection  5.960E-06 0.0       1     
======================== ========= ========= ======