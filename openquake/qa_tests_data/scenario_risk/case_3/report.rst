Scenario QA Test 3
==================

============== ===================
checksum32     3,085,599,105      
date           2018-03-26T15:57:41
engine_version 2.10.0-git543cfb0  
============== ===================

num_sites = 4, num_levels = 15

Parameters
----------
=============================== ==================
calculation_mode                'scenario_risk'   
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 300.0}
investigation_time              None              
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            10.0              
complex_fault_mesh_spacing      10.0              
width_of_mfd_bin                None              
area_source_discretization      None              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     3                 
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
rupture_model            `fault_rupture.xml <fault_rupture.xml>`_            
structural_vulnerability `vulnerability_model.xml <vulnerability_model.xml>`_
======================== ====================================================

Composite source model
----------------------
========= ====== =============== ================
smlt_path weight gsim_logic_tree num_realizations
========= ====== =============== ================
b_1       1.000  trivial(1)      1/1             
========= ====== =============== ================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)
  0,ChiouYoungs2008(): [0]>

Exposure model
--------------
=============== ========
#assets         4       
#taxonomies     3       
deductibile     absolute
insurance_limit absolute
=============== ========

======== ===== ====== === === ========= ==========
taxonomy mean  stddev min max num_sites num_assets
RM       1.000 NaN    1   1   1         1         
RC       1.000 NaN    1   1   1         1         
W        1.000 0.0    1   1   2         2         
*ALL*    1.000 0.0    1   1   4         4         
======== ===== ====== === === ========= ==========

Slowest operations
------------------
======================= ========= ========= ======
operation               time_sec  memory_mb counts
======================= ========= ========= ======
saving gmfs             0.038     0.0       1     
building riskinputs     0.027     0.0       1     
computing gmfs          0.009     0.0       1     
reading exposure        0.008     0.0       1     
building epsilons       9.665E-04 0.0       1     
reading site collection 5.507E-05 0.0       1     
======================= ========= ========= ======