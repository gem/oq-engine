Scenario Risk Test
==================

============== ===================
checksum32     4_057_024_737      
date           2020-01-16T05:30:43
engine_version 3.8.0-git83c45f7244
============== ===================

num_sites = 27, num_levels = 8, num_rlzs = 1

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
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
b_1       1.00000 trivial(1)      1               
========= ======= =============== ================

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)>

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
calc_43220          time_sec  memory_mb counts
=================== ========= ========= ======
building riskinputs 0.00517   0.0       1     
reading exposure    6.394E-04 0.0       1     
=================== ========= ========= ======