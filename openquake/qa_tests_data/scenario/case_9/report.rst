Scenario QA Test, Case 9, Multiple GSIMs
========================================

gem-tstation:/home/michele/ssd/calc_16306.hdf5 updated Mon May 16 14:19:02 2016

num_sites = 3, sitecol = 831 B

Parameters
----------
============================ ===================
calculation_mode             'scenario'         
number_of_logic_tree_samples 0                  
maximum_distance             {'default': 200}   
investigation_time           None               
ses_per_logic_tree_path      1                  
truncation_level             1.0                
rupture_mesh_spacing         1.0                
complex_fault_mesh_spacing   1.0                
width_of_mfd_bin             None               
area_source_discretization   None               
random_seed                  3                  
master_seed                  0                  
oqlite_version               '0.13.0-git16c052c'
============================ ===================

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

  <RlzsAssoc(2)
  0,LinLee2008SSlab(): ['LinLee2008SSlab()']
  0,YoungsEtAl1997SSlab(): ['YoungsEtAl1997SSlab()']>

Information about the tasks
---------------------------
Not available

Slowest operations
------------------
======================= ========= ========= ======
operation               time_sec  memory_mb counts
======================= ========= ========= ======
filtering sites         0.276     0.0       1     
computing gmfs          0.004     0.0       1     
reading site collection 7.606E-05 0.0       1     
======================= ========= ========= ======