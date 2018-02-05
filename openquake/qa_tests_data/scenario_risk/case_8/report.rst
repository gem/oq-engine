Scenario Risk Maule Mw 8.8 reduced
==================================

============== ===================
checksum32     4,058,514,510      
date           2018-02-02T16:04:43
engine_version 2.9.0-gitd6a3184   
============== ===================

num_sites = 29, num_levels = 78

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
random_seed                     113            
master_seed                     0              
avg_losses                      True           
=============================== ===============

Input files
-----------
======================== ==================================================================================
Name                     File                                                                              
======================== ==================================================================================
exposure                 `exposure_model.xml <exposure_model.xml>`_                                        
gmfs                     `GMFs_Mabe.xml <GMFs_Mabe.xml>`_                                                  
job_ini                  `job.ini <job.ini>`_                                                              
occupants_vulnerability  `occupants_vulnerabilityRes.xml <occupants_vulnerabilityRes.xml>`_                
sites                    `sites.csv <sites.csv>`_                                                          
structural_vulnerability `structural_vulnerability_model_Res.xml <structural_vulnerability_model_Res.xml>`_
======================== ==================================================================================

Composite source model
----------------------
========= ====== =============== ================
smlt_path weight gsim_logic_tree num_realizations
========= ====== =============== ================
b_1       1.000  trivial(1)      1/1             
========= ====== =============== ================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)
  0,FromFile: [0]>

Exposure model
--------------
=============== ========
#assets         56      
#taxonomies     31      
deductibile     absolute
insurance_limit absolute
=============== ========

======== ===== ====== === === ========= ==========
taxonomy mean  stddev min max num_sites num_assets
1        1.000 0.0    1   1   2         2         
2        1.000 NaN    1   1   1         1         
3        1.000 0.0    1   1   3         3         
4        1.000 0.0    1   1   3         3         
5        1.000 0.0    1   1   3         3         
6        1.000 0.0    1   1   2         2         
7        1.000 0.0    1   1   2         2         
8        1.000 NaN    1   1   1         1         
9        1.000 0.0    1   1   2         2         
10       1.000 0.0    1   1   3         3         
11       2.000 NaN    2   2   1         2         
12       1.000 NaN    1   1   1         1         
13       1.000 0.0    1   1   2         2         
14       1.000 0.0    1   1   2         2         
15       1.000 0.0    1   1   3         3         
16       1.000 NaN    1   1   1         1         
17       1.000 0.0    1   1   4         4         
18       1.500 0.707  1   2   2         3         
19       1.000 NaN    1   1   1         1         
21       1.000 0.0    1   1   2         2         
22       1.000 NaN    1   1   1         1         
23       1.000 0.0    1   1   2         2         
24       1.000 NaN    1   1   1         1         
25       1.000 NaN    1   1   1         1         
26       1.000 0.0    1   1   2         2         
27       1.000 NaN    1   1   1         1         
28       1.000 NaN    1   1   1         1         
29       1.000 NaN    1   1   1         1         
30       1.000 NaN    1   1   1         1         
32       1.000 NaN    1   1   1         1         
33       1.000 NaN    1   1   1         1         
*ALL*    0.217 0.743  0   6   258       56        
======== ===== ====== === === ========= ==========

Slowest operations
------------------
======================= ======== ========= ======
operation               time_sec memory_mb counts
======================= ======== ========= ======
assoc_assets_sites      0.054    0.0       2     
building riskinputs     0.043    0.0       1     
reading exposure        0.015    0.0       1     
building epsilons       0.002    0.0       1     
reading site collection 0.001    0.0       1     
======================= ======== ========= ======