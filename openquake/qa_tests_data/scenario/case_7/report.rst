Scenario QA Test with No Spatial Correlation
============================================

======================================== ========================
localhost:/mnt/ssd/oqdata/calc_7562.hdf5 Wed Apr 26 15:54:20 2017
engine_version                           2.4.0-git9336bd0        
hazardlib_version                        0.24.0-gita895d4c       
======================================== ========================

num_sites = 2, sitecol = 863 B

Parameters
----------
=============================== ==================
calculation_mode                'scenario'        
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              None              
ses_per_logic_tree_path         1                 
truncation_level                None              
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
============= ========================================
Name          File                                    
============= ========================================
job_ini       `job.ini <job.ini>`_                    
rupture_model `rupture_model.xml <rupture_model.xml>`_
============= ========================================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)
  0,BooreAtkinson2008(): ['<0,b_1~b1,w=1.0>']>

Slowest operations
------------------
======================= ========= ========= ======
operation               time_sec  memory_mb counts
======================= ========= ========= ======
filtering sites         0.008     0.0       1     
reading site collection 3.123E-05 0.0       1     
======================= ========= ========= ======