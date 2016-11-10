Scenario Risk for Nepal with 20 assets
======================================

============================================== ========================
gem-tstation:/home/michele/ssd/calc_67016.hdf5 Wed Nov  9 08:16:41 2016
engine_version                                 2.2.0-git54d01f4        
hazardlib_version                              0.22.0-git173c60c       
============================================== ========================

num_sites = 20, sitecol = 1.58 KB

Parameters
----------
============================ =================
calculation_mode             'scenario_risk'  
number_of_logic_tree_samples 0                
maximum_distance             {u'default': 500}
investigation_time           None             
ses_per_logic_tree_path      1                
truncation_level             3.0              
rupture_mesh_spacing         15.0             
complex_fault_mesh_spacing   15.0             
width_of_mfd_bin             None             
area_source_discretization   None             
random_seed                  42               
master_seed                  0                
avg_losses                   False            
============================ =================

Input files
-----------
======================== ==========================================================================
Name                     File                                                                      
======================== ==========================================================================
exposure                 `exposure_model.xml <exposure_model.xml>`_                                
job_ini                  `job.ini <job.ini>`_                                                      
rupture_model            `fault_rupture.xml <fault_rupture.xml>`_                                  
structural_vulnerability `structural_vulnerability_model.xml <structural_vulnerability_model.xml>`_
======================== ==========================================================================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)
  0,ChiouYoungs2008(): ['<0,b_1~b1,w=1.0>']>

Exposure model
--------------
=============== ========
#assets         20      
#taxonomies     4       
deductibile     relative
insurance_limit relative
=============== ========

========================== ===== ====== === === ========= ==========
taxonomy                   mean  stddev min max num_sites num_assets
Adobe                      1.000 0.0    1   1   3         3         
Stone-Masonry              1.000 0.0    1   1   4         4         
Unreinforced-Brick-Masonry 1.000 0.0    1   1   5         5         
Wood                       1.000 0.0    1   1   8         8         
*ALL*                      1.000 0.0    1   1   20        20        
========================== ===== ====== === === ========= ==========

Slowest operations
------------------
======================= ========= ========= ======
operation               time_sec  memory_mb counts
======================= ========= ========= ======
reading exposure        0.008     0.0       1     
filtering sites         0.004     0.0       1     
computing gmfs          0.003     0.0       1     
saving gmfs             0.001     0.0       1     
building riskinputs     8.268E-04 0.0       1     
building epsilons       3.510E-04 0.0       1     
reading site collection 6.914E-06 0.0       1     
======================= ========= ========= ======