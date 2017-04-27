Scenario QA Test 3
==================

=============================================== ========================
tstation.gem.lan:/mnt/ssd/oqdata/calc_7638.hdf5 Wed Apr 26 15:56:32 2017
engine_version                                  2.4.0-git9336bd0        
hazardlib_version                               0.24.0-gita895d4c       
=============================================== ========================

num_sites = 4, sitecol = 971 B

Parameters
----------
=============================== ==================
calculation_mode                'scenario_risk'   
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 300.0}
investigation_time              None              
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            10.0              
complex_fault_mesh_spacing      10.0              
width_of_mfd_bin                None              
area_source_discretization      None              
ground_motion_correlation_model None              
random_seed                     3                 
master_seed                     0                 
avg_losses                      False             
=============================== ==================

Input files
-----------
======================== ====================================================
Name                     File                                                
======================== ====================================================
exposure                 `exposure_model.xml <exposure_model.xml>`_          
job_ini                  `job.ini <job.ini>`_                                
rupture_model            `fault_rupture.xml <fault_rupture.xml>`_            
structural_vulnerability `vulnerability_model.xml <vulnerability_model.xml>`_
======================== ====================================================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)
  0,ChiouYoungs2008(): ['<0,b_1~b1,w=1.0>']>

Informational data
------------------
================ ================
hostname         tstation.gem.lan
require_epsilons 0 B             
================ ================

Exposure model
--------------
=============== ========
#assets         4       
#taxonomies     3       
deductibile     absolute
insurance_limit absolute
=============== ========

======== ===== ====== === === ========= ==========
taxonomy mean  stddev min max num_sites num_assets
RC       1.000 NaN    1   1   1         1         
RM       1.000 NaN    1   1   1         1         
W        1.000 0.0    1   1   2         2         
*ALL*    1.000 0.0    1   1   4         4         
======== ===== ====== === === ========= ==========

Slowest operations
------------------
======================== ========= ========= ======
operation                time_sec  memory_mb counts
======================== ========= ========= ======
computing gmfs           0.073     0.0       1     
filtering sites          0.005     0.0       1     
building site collection 0.005     0.0       1     
reading exposure         0.002     0.0       1     
saving gmfs              0.001     0.0       1     
building epsilons        5.524E-04 0.0       1     
building riskinputs      2.615E-04 0.0       1     
reading site collection  7.629E-06 0.0       1     
======================== ========= ========= ======