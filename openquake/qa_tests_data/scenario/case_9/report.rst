Scenario QA Test, Case 9, Multiple GSIMs
========================================

======================================== ========================
localhost:/mnt/ssd/oqdata/calc_7558.hdf5 Wed Apr 26 15:54:20 2017
engine_version                           2.4.0-git9336bd0        
hazardlib_version                        0.24.0-gita895d4c       
======================================== ========================

num_sites = 3, sitecol = 917 B

Parameters
----------
=============================== ==================
calculation_mode                'scenario'        
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              None              
ses_per_logic_tree_path         1                 
truncation_level                1.0               
rupture_mesh_spacing            1.0               
complex_fault_mesh_spacing      1.0               
width_of_mfd_bin                None              
area_source_discretization      None              
ground_motion_correlation_model None              
random_seed                     3                 
master_seed                     0                 
=============================== ==================

Input files
-----------
=============== ============================================
Name            File                                        
=============== ============================================
gsim_logic_tree `gsim_logic_tree.xml <gsim_logic_tree.xml>`_
job_ini         `job.ini <job.ini>`_                        
rupture_model   `rupture_model.xml <rupture_model.xml>`_    
=============== ============================================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=2, rlzs=2)
  0,LinLee2008SSlab(): ['<0,b_1~b1,w=0.6>']
  0,YoungsEtAl1997SSlab(): ['<1,b_1~b2,w=0.4>']>

Slowest operations
------------------
======================= ========= ========= ======
operation               time_sec  memory_mb counts
======================= ========= ========= ======
filtering sites         0.011     0.0       1     
reading site collection 3.242E-05 0.0       1     
======================= ========= ========= ======