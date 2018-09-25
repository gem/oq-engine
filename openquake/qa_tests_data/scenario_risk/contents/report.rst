QA Scenario Risk for contents
=============================

============== ===================
checksum32     3,665,953,184      
date           2018-09-25T14:27:44
engine_version 3.3.0-git8ffb37de56
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

Slowest operations
------------------
=================== ========= ========= ======
operation           time_sec  memory_mb counts
=================== ========= ========= ======
building riskinputs 0.00417   0.0       1     
computing gmfs      0.00334   0.0       1     
saving gmfs         0.00137   0.0       1     
reading exposure    4.015E-04 0.0       1     
=================== ========= ========= ======