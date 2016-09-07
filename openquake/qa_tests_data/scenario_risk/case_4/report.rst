Scenario Risk for Nepal with 20 assets
======================================

============================================== ================================
gem-tstation:/home/michele/ssd/calc_48317.hdf5 updated Wed Sep  7 15:57:57 2016
engine_version                                 2.1.0-git3a14ca6                
hazardlib_version                              0.21.0-git89bccaf               
============================================== ================================

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

Information about the tasks
---------------------------
Not available

Slowest operations
------------------
======================= ========= ========= ======
operation               time_sec  memory_mb counts
======================= ========= ========= ======
reading exposure        0.015     0.0       1     
filtering sites         0.006     0.0       1     
computing gmfs          0.005     0.0       1     
saving gmfs             0.002     0.0       1     
building riskinputs     8.969E-04 0.0       1     
building epsilons       4.718E-04 0.0       1     
reading site collection 1.311E-05 0.0       1     
======================= ========= ========= ======