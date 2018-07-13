Scenario Risk Test
==================

============== ===================
checksum32     4,057,024,737      
date           2018-06-26T14:58:40
engine_version 3.2.0-gitb0cd949   
============== ===================

num_sites = 27, num_levels = 8

Parameters
----------
=============================== ===============
calculation_mode                'scenario_risk'
number_of_logic_tree_samples    0              
maximum_distance                None           
investigation_time              None           
ses_per_logic_tree_path         1              
truncation_level                None           
rupture_mesh_spacing            None           
complex_fault_mesh_spacing      None           
width_of_mfd_bin                None           
area_source_discretization      None           
ground_motion_correlation_model None           
minimum_intensity               {}             
random_seed                     42             
master_seed                     0              
ses_seed                        42             
avg_losses                      True           
=============================== ===============

Input files
-----------
======================== ================================================================
Name                     File                                                            
======================== ================================================================
exposure                 `exposurePathSines.xml <exposurePathSines.xml>`_                
gmfs                     `gmfs.csv <gmfs.csv>`_                                          
job_ini                  `job.ini <job.ini>`_                                            
structural_vulnerability `vulnerability_model_test1.xml <vulnerability_model_test1.xml>`_
======================== ================================================================

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
  0,FromFile: [0]>

Exposure model
--------------
=============== ========
#assets         27      
#taxonomies     4       
deductibile     absolute
insurance_limit absolute
=============== ========

======== ======= ====== === === ========= ==========
taxonomy mean    stddev min max num_sites num_assets
2        1.00000 0.0    1   1   4         4         
4        1.00000 0.0    1   1   16        16        
3        1.00000 0.0    1   1   5         5         
1        1.00000 0.0    1   1   2         2         
*ALL*    1.00000 0.0    1   1   27        27        
======== ======= ====== === === ========= ==========

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =========
operation-duration mean    stddev  min     max     num_tasks
scenario_risk      0.00716 0.00302 0.00278 0.01407 27       
================== ======= ======= ======= ======= =========

Data transfer
-------------
============= =================================================================== ========
task          sent                                                                received
scenario_risk riskinput=73.62 KB riskmodel=51.76 KB monitor=11.1 KB param=2.35 KB 16.85 KB
============= =================================================================== ========

Slowest operations
------------------
======================== ======== ========= ======
operation                time_sec memory_mb counts
======================== ======== ========= ======
total scenario_risk      0.19336  2.33594   27    
computing risk           0.06923  0.43359   27    
building riskinputs      0.04854  0.0       1     
getting hazard           0.02067  0.0       54    
unpickling scenario_risk 0.00763  0.0       27    
reading site collection  0.00584  0.0       1     
reading exposure         0.00320  0.0       1     
building epsilons        0.00114  0.0       1     
======================== ======== ========= ======