Scenario QA Test, Case 1
========================

============================================== ========================
gem-tstation:/home/michele/ssd/calc_80519.hdf5 Thu Jan 26 05:24:18 2017
engine_version                                 2.3.0-gitd31dc69        
hazardlib_version                              0.23.0-git4d14bee       
============================================== ========================

num_sites = 3, sitecol = 854 B

Parameters
----------
=============================== ================
calculation_mode                'scenario'      
number_of_logic_tree_samples    0               
maximum_distance                {'default': 200}
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
=============================== ================

Input files
-----------
============= ========================================
Name          File                                    
============= ========================================
job_ini       `job.ini <job.ini>`_                    
rupture_model `rupture_model.xml <rupture_model.xml>`_
site_model    `site_model.xml <site_model.xml>`_      
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
filtering sites         0.011     0.0       1     
reading site collection 7.308E-04 0.0       1     
======================= ========= ========= ======