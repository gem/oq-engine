Calculation of the ground motion fields for a scenario
======================================================

======================================== ========================
localhost:/mnt/ssd/oqdata/calc_7554.hdf5 Wed Apr 26 15:54:20 2017
engine_version                           2.4.0-git9336bd0        
hazardlib_version                        0.24.0-gita895d4c       
======================================== ========================

num_sites = 7, sitecol = 1.39 KB

Parameters
----------
=============================== ==================
calculation_mode                'scenario'        
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              None              
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            15.0              
complex_fault_mesh_spacing      15.0              
width_of_mfd_bin                None              
area_source_discretization      None              
ground_motion_correlation_model None              
random_seed                     3                 
master_seed                     0                 
=============================== ==================

Input files
-----------
============= ==========================================
Name          File                                      
============= ==========================================
exposure      `exposure_model.xml <exposure_model.xml>`_
job_ini       `job_haz.ini <job_haz.ini>`_              
rupture_model `fault_rupture.xml <fault_rupture.xml>`_  
============= ==========================================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)
  0,ChiouYoungs2008(): ['<0,b_1~b1,w=1.0>']>

Exposure model
--------------
=============== ========
#assets         11      
#taxonomies     4       
deductibile     relative
insurance_limit relative
=============== ========

======== ===== ====== === === ========= ==========
taxonomy mean  stddev min max num_sites num_assets
A        1.000 0.0    1   1   5         5         
DS       1.000 0.0    1   1   2         2         
UFB      1.000 0.0    1   1   2         2         
W        1.000 0.0    1   1   2         2         
*ALL*    1.000 0.0    1   1   11        11        
======== ===== ====== === === ========= ==========

Slowest operations
------------------
======================== ========= ========= ======
operation                time_sec  memory_mb counts
======================== ========= ========= ======
building site collection 0.004     0.0       1     
filtering sites          0.003     0.0       1     
reading exposure         0.002     0.0       1     
reading site collection  5.722E-06 0.0       1     
======================== ========= ========= ======