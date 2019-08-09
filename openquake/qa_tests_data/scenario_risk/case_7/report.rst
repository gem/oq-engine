Scenario Risk Test
==================

============== ===================
checksum32     4,057,024,737      
date           2019-07-30T15:03:55
engine_version 3.7.0-git3b3dff46da
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

Number of ruptures per tectonic region type
-------------------------------------------
============ ====== === ============ ============
source_model grp_id trt eff_ruptures tot_ruptures
============ ====== === ============ ============
scenario     0      *   1            0           
============ ====== === ============ ============

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

Slowest operations
------------------
=================== ========= ========= ======
calc_15497          time_sec  memory_mb counts
=================== ========= ========= ======
building riskinputs 0.03479   0.0       1     
reading exposure    5.906E-04 0.0       1     
=================== ========= ========= ======