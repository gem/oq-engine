scenario risk
=============

============== ===================
checksum32     1,429,593,239      
date           2018-05-15T04:14:23
engine_version 3.1.0-git0acbc11   
============== ===================

num_sites = 2, num_levels = 8

Parameters
----------
=============================== ==================
calculation_mode                'scenario_risk'   
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              None              
ses_per_logic_tree_path         1                 
truncation_level                0.0               
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                None              
area_source_discretization      None              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     42                
master_seed                     0                 
ses_seed                        42                
avg_losses                      True              
=============================== ==================

Input files
-----------
======================== ====================================================
Name                     File                                                
======================== ====================================================
exposure                 `exposure_model.xml <exposure_model.xml>`_          
job_ini                  `job.ini <job.ini>`_                                
rupture_model            `rupture_model.xml <rupture_model.xml>`_            
structural_vulnerability `vulnerability_model.xml <vulnerability_model.xml>`_
======================== ====================================================

Composite source model
----------------------
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
b_1       1.00000 trivial(1)      1/1             
========= ======= =============== ================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)
  0,BooreAtkinson2008(): [0]>

Exposure model
--------------
=============== ========
#assets         2       
#taxonomies     1       
deductibile     absolute
insurance_limit absolute
=============== ========

======== ======= ====== === === ========= ==========
taxonomy mean    stddev min max num_sites num_assets
tax1     1.00000 0.0    1   1   2         2         
======== ======= ====== === === ========= ==========

Slowest operations
------------------
======================= ========= ========= ======
operation               time_sec  memory_mb counts
======================= ========= ========= ======
building riskinputs     0.01043   0.0       1     
saving gmfs             0.00405   0.0       1     
reading site collection 0.00303   0.0       1     
reading exposure        0.00131   0.0       1     
building epsilons       3.765E-04 0.0       1     
computing gmfs          3.695E-04 0.0       1     
======================= ========= ========= ======