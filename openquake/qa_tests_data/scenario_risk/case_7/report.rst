Scenario Risk Test
==================

======================================== ========================
localhost:/mnt/ssd/oqdata/calc_7642.hdf5 Wed Apr 26 15:56:32 2017
engine_version                           2.4.0-git9336bd0        
hazardlib_version                        0.24.0-gita895d4c       
======================================== ========================

num_sites = 27, sitecol = 2.16 KB

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
random_seed                     42             
master_seed                     0              
avg_losses                      False          
=============================== ===============

Input files
-----------
======================== ================================================================
Name                     File                                                            
======================== ================================================================
exposure                 `exposurePathSines.xml <exposurePathSines.xml>`_                
gmfs                     `GMF_results_smallTest.txt <GMF_results_smallTest.txt>`_        
job_ini                  `job.ini <job.ini>`_                                            
structural_vulnerability `vulnerability_model_test1.xml <vulnerability_model_test1.xml>`_
======================== ================================================================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)
  0,FromFile: ['<0,b_1~b1,w=1.0>']>

Exposure model
--------------
=============== ========
#assets         27      
#taxonomies     4       
deductibile     absolute
insurance_limit absolute
=============== ========

======== ===== ====== === === ========= ==========
taxonomy mean  stddev min max num_sites num_assets
1        1.000 0.0    1   1   2         2         
2        1.000 0.0    1   1   4         4         
3        1.000 0.0    1   1   5         5         
4        1.000 0.0    1   1   16        16        
*ALL*    1.000 0.0    1   1   27        27        
======== ===== ====== === === ========= ==========

Slowest operations
------------------
======================== ========= ========= ======
operation                time_sec  memory_mb counts
======================== ========= ========= ======
assoc_assets_sites       0.007     0.0       1     
building site collection 0.004     0.0       1     
reading exposure         0.003     0.0       1     
reading site collection  0.002     0.0       1     
building riskinputs      9.100E-04 0.0       1     
building epsilons        4.745E-04 0.0       1     
======================== ========= ========= ======