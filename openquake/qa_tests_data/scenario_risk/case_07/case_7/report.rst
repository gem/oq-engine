Scenario Risk Test
==================

============== ====================
checksum32     648_091_558         
date           2020-11-02T09:35:34 
engine_version 3.11.0-git82b78631ac
============== ====================

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
pointsource_distance            None           
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
====== ============ ====
grp_id gsim         rlzs
====== ============ ====
0      '[FromFile]' [0] 
====== ============ ====

Exposure model
--------------
=========== ==
#assets     27
#taxonomies 4 
=========== ==

======== ========== ======= ====== === === =========
taxonomy num_assets mean    stddev min max num_sites
2        4          1.00000 0%     1   1   4        
4        16         1.00000 0%     1   1   16       
3        5          1.00000 0%     1   1   5        
1        2          1.00000 0%     1   1   2        
*ALL*    27         1.00000 0%     1   1   27       
======== ========== ======= ====== === === =========

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
calc_47237          time_sec  memory_mb counts
=================== ========= ========= ======
building riskinputs 0.02834   0.99219   1     
importing inputs    0.02251   0.0       1     
reading GMFs        0.00972   0.92969   1     
reading exposure    6.976E-04 0.0       1     
=================== ========= ========= ======