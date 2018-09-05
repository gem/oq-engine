scenario risk
=============

============== ===================
checksum32     1,429,593,239      
date           2018-09-05T10:03:41
engine_version 3.2.0-gitb4ef3a4b6c
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

Information about the tasks
---------------------------
================== ======= ========= ======= ======= =========
operation-duration mean    stddev    min     max     num_tasks
scenario_risk      0.07966 5.467E-04 0.07928 0.08005 2        
================== ======= ========= ======= ======= =========

Data transfer
-------------
============= =============================================================== ========
task          sent                                                            received
scenario_risk riskinputs=15.06 KB riskmodel=2.62 KB monitor=618 B param=220 B 1.6 KB  
============= =============================================================== ========

Slowest operations
------------------
=================== ========= ========= ======
operation           time_sec  memory_mb counts
=================== ========= ========= ======
total scenario_risk 0.15933   1.40234   2     
computing risk      0.15709   1.40234   2     
building riskinputs 0.00378   0.0       1     
saving gmfs         0.00217   0.0       1     
getting hazard      8.013E-04 0.0       4     
reading exposure    5.710E-04 0.0       1     
computing gmfs      5.643E-04 0.0       1     
=================== ========= ========= ======