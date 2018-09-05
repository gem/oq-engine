QA Scenario Risk for contents
=============================

============== ===================
checksum32     3,665,953,184      
date           2018-09-05T10:03:41
engine_version 3.2.0-gitb4ef3a4b6c
============== ===================

num_sites = 3, num_levels = 20

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
======================== ========================================================================
Name                     File                                                                    
======================== ========================================================================
contents_vulnerability   `vulnerability_model_contents.xml <vulnerability_model_contents.xml>`_  
exposure                 `exposure_model.xml <exposure_model.xml>`_                              
job_ini                  `job.ini <job.ini>`_                                                    
rupture_model            `fault_rupture.xml <fault_rupture.xml>`_                                
structural_vulnerability `vulnerability_model_structure.xml <vulnerability_model_structure.xml>`_
======================== ========================================================================

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
#assets         3       
#taxonomies     3       
deductibile     absolute
insurance_limit absolute
=============== ========

======== ======= ====== === === ========= ==========
taxonomy mean    stddev min max num_sites num_assets
RM       1.00000 NaN    1   1   1         1         
RC       1.00000 NaN    1   1   1         1         
W        1.00000 NaN    1   1   1         1         
*ALL*    1.00000 0.0    1   1   3         3         
======== ======= ====== === === ========= ==========

Information about the tasks
---------------------------
================== ======= ========= ======= ======= =========
operation-duration mean    stddev    min     max     num_tasks
scenario_risk      0.00365 3.409E-04 0.00327 0.00392 3        
================== ======= ========= ======= ======= =========

Data transfer
-------------
============= ============================================================== ========
task          sent                                                           received
scenario_risk riskinputs=8.94 KB riskmodel=6.39 KB monitor=927 B param=330 B 1.6 KB  
============= ============================================================== ========

Slowest operations
------------------
=================== ========= ========= ======
operation           time_sec  memory_mb counts
=================== ========= ========= ======
total scenario_risk 0.01095   0.28516   3     
computing risk      0.00804   0.28516   3     
building riskinputs 0.00480   0.0       1     
computing gmfs      0.00317   0.0       1     
saving gmfs         0.00135   0.0       1     
getting hazard      9.837E-04 0.0       6     
reading exposure    4.225E-04 0.00391   1     
=================== ========= ========= ======