Scenario Calculation with Simple Fault Rupture
==============================================

gem-tstation:/home/michele/ssd/calc_16299.hdf5 updated Mon May 16 14:19:01 2016

num_sites = 1, sitecol = 739 B

Parameters
----------
============================ ===================
calculation_mode             'scenario'         
number_of_logic_tree_samples 0                  
maximum_distance             {'default': 200}   
investigation_time           None               
ses_per_logic_tree_path      1                  
truncation_level             3.0                
rupture_mesh_spacing         2.0                
complex_fault_mesh_spacing   2.0                
width_of_mfd_bin             None               
area_source_discretization   None               
random_seed                  42                 
master_seed                  0                  
oqlite_version               '0.13.0-git16c052c'
============================ ===================

Input files
-----------
=============== ============================================
Name            File                                        
=============== ============================================
gsim_logic_tree `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_
job_ini         `job_haz.ini <job_haz.ini>`_                
rupture_model   `rupture_model.xml <rupture_model.xml>`_    
=============== ============================================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(2)
  0,BooreAtkinson2008(): ['BooreAtkinson2008()']
  0,ChiouYoungs2008(): ['ChiouYoungs2008()']>

Information about the tasks
---------------------------
Not available

Slowest operations
------------------
======================= ========= ========= ======
operation               time_sec  memory_mb counts
======================= ========= ========= ======
filtering sites         0.008     0.0       1     
computing gmfs          0.002     0.0       1     
reading site collection 3.910E-05 0.0       1     
======================= ========= ========= ======