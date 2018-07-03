scenario risk
=============

============== ===================
checksum32     1,429,593,239      
date           2018-06-26T14:58:37
engine_version 3.2.0-gitb0cd949   
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
================== ======= ======= ======= ======= =========
operation-duration mean    stddev  min     max     num_tasks
scenario_risk      0.09501 0.00614 0.09066 0.09935 2        
================== ======= ======= ======= ======= =========

Data transfer
-------------
============= ============================================================= ========
task          sent                                                          received
scenario_risk riskinput=5.11 KB riskmodel=2.62 KB monitor=842 B param=178 B 1.6 KB  
============= ============================================================= ========

Slowest operations
------------------
======================== ========= ========= ======
operation                time_sec  memory_mb counts
======================== ========= ========= ======
total scenario_risk      0.19001   7.26953   2     
computing risk           0.17007   0.80859   2     
getting hazard           0.01496   5.17578   4     
building riskinputs      0.00156   0.0       1     
unpickling scenario_risk 9.375E-04 0.0       2     
building epsilons        4.532E-04 0.0       1     
======================== ========= ========= ======