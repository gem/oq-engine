Scenario QA Test 3
==================

============== ===================
checksum32     775,322,845        
date           2018-09-05T10:03:41
engine_version 3.2.0-gitb4ef3a4b6c
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
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
b_1       1.00000 trivial(1)      1/1             
========= ======= =============== ================

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

======== ======= ====== === === ========= ==========
taxonomy mean    stddev min max num_sites num_assets
RM       1.00000 NaN    1   1   1         1         
RC       1.00000 NaN    1   1   1         1         
W        1.00000 0.0    1   1   2         2         
*ALL*    1.00000 0.0    1   1   4         4         
======== ======= ====== === === ========= ==========

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =========
operation-duration mean    stddev  min     max     num_tasks
scenario_risk      0.00509 0.00123 0.00348 0.00647 4        
================== ======= ======= ======= ======= =========

Data transfer
-------------
============= ================================================================== ========
task          sent                                                               received
scenario_risk riskinputs=477.02 KB riskmodel=5.59 KB monitor=1.21 KB param=444 B 32.72 KB
============= ================================================================== ========

Slowest operations
------------------
=================== ========= ========= ======
operation           time_sec  memory_mb counts
=================== ========= ========= ======
saving gmfs         0.02873   0.0       1     
total scenario_risk 0.02034   0.18750   4     
building riskinputs 0.01789   0.0       1     
computing risk      0.01493   0.18750   4     
computing gmfs      0.00666   0.0       1     
getting hazard      0.00199   0.0       8     
reading exposure    4.272E-04 0.0       1     
=================== ========= ========= ======