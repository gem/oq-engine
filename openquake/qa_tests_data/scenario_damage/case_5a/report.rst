Scenario Calculation with Simple Fault Rupture
==============================================

============================================== ========================
gem-tstation:/home/michele/ssd/calc_66935.hdf5 Wed Nov  9 08:14:03 2016
engine_version                                 2.2.0-git54d01f4        
hazardlib_version                              0.22.0-git173c60c       
============================================== ========================

num_sites = 1, sitecol = 739 B

Parameters
----------
============================ =================
calculation_mode             'scenario'       
number_of_logic_tree_samples 0                
maximum_distance             {u'default': 200}
investigation_time           None             
ses_per_logic_tree_path      1                
truncation_level             3.0              
rupture_mesh_spacing         2.0              
complex_fault_mesh_spacing   2.0              
width_of_mfd_bin             None             
area_source_discretization   None             
random_seed                  42               
master_seed                  0                
============================ =================

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

  <RlzsAssoc(size=2, rlzs=2)
  0,BooreAtkinson2008(): ['<0,b_1~b1,w=0.75>']
  0,ChiouYoungs2008(): ['<1,b_1~b2,w=0.25>']>

Slowest operations
------------------
======================= ========= ========= ======
operation               time_sec  memory_mb counts
======================= ========= ========= ======
filtering sites         0.008     0.0       1     
reading site collection 3.886E-05 0.0       1     
======================= ========= ========= ======