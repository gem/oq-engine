Scenario Risk Test
==================

============== ===================
checksum32     4_057_024_737      
date           2020-03-13T11:20:19
engine_version 3.9.0-gitfb3ef3a732
============== ===================

num_sites = 27, num_levels = 1, num_rlzs = 1

Parameters
----------
=============================== ===============
calculation_mode                'scenario_risk'
number_of_logic_tree_samples    0              
maximum_distance                None           
investigation_time              None           
ses_per_logic_tree_path         1              
truncation_level                None           
rupture_mesh_spacing            5.0            
complex_fault_mesh_spacing      5.0            
width_of_mfd_bin                None           
area_source_discretization      None           
pointsource_distance            {'default': {}}
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
========= ======= ================
smlt_path weight  num_realizations
========= ======= ================
b_1       1.00000 1               
========= ======= ================

Exposure model
--------------
=========== ==
#assets     27
#taxonomies 4 
=========== ==

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
Not available

Data transfer
-------------
==== ==== ========
task sent received
==== ==== ========

Slowest operations
------------------
=================== ========= ========= ======
calc_66887          time_sec  memory_mb counts
=================== ========= ========= ======
building riskinputs 0.00481   0.0       1     
reading exposure    6.382E-04 0.0       1     
=================== ========= ========= ======