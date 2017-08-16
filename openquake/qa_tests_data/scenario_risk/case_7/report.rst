Scenario Risk Test
==================

========================================= ========================
localhost:/mnt/ssd/oqdata/calc_29162.hdf5 Wed Jun 14 10:01:42 2017
engine_version                            2.5.0-gite200a20        
========================================= ========================

num_sites = 27, num_imts = 1

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
======================= ========= ========= ======
operation               time_sec  memory_mb counts
======================= ========= ========= ======
assoc_assets_sites      0.007     0.0       1     
reading exposure        0.007     0.0       1     
reading site collection 0.002     0.0       1     
building riskinputs     0.001     0.0       1     
building epsilons       4.847E-04 0.0       1     
======================= ========= ========= ======