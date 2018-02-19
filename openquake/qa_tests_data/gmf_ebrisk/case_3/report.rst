Event Based Risk from GMF
=========================

============== ===================
checksum32     692,252,974        
date           2018-02-16T05:47:30
engine_version 2.9.0-git1a21ce0   
============== ===================

num_sites = 11, num_levels = 170

Parameters
----------
=============================== ==================
calculation_mode                'event_based_risk'
number_of_logic_tree_samples    0                 
maximum_distance                None              
investigation_time              1.0               
ses_per_logic_tree_path         1                 
truncation_level                None              
rupture_mesh_spacing            None              
complex_fault_mesh_spacing      None              
width_of_mfd_bin                None              
area_source_discretization      None              
ground_motion_correlation_model None              
random_seed                     42                
master_seed                     0                 
avg_losses                      True              
=============================== ==================

Input files
-----------
======================== ======================================================
Name                     File                                                  
======================== ======================================================
exposure                 `expo_CR_60_SJ.xml <expo_CR_60_SJ.xml>`_              
gmfs                     `gmfs.csv <gmfs.csv>`_                                
job_ini                  `job.ini <job.ini>`_                                  
sites                    `sitemesh_SJ_60arcsec.csv <sitemesh_SJ_60arcsec.csv>`_
structural_vulnerability `cr_vulnerability_v5.xml <cr_vulnerability_v5.xml>`_  
======================== ======================================================

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

Estimated data transfer for the avglosses
-----------------------------------------
34 asset(s) x 1 realization(s) x 1 loss type(s) x 1 losses x 8 bytes x 60 tasks = 15.94 KB

Exposure model
--------------
=============== ========
#assets         34      
#taxonomies     10      
deductibile     absolute
insurance_limit absolute
=============== ========

======== ===== ====== === === ========= ==========
taxonomy mean  stddev min max num_sites num_assets
1        1.000 0.0    1   1   2         2         
2        1.333 0.577  1   2   3         4         
3        1.200 0.447  1   2   5         6         
4        1.500 0.577  1   2   4         6         
5        1.500 0.707  1   2   2         3         
6        1.000 0.0    1   1   3         3         
7        1.000 0.0    1   1   2         2         
8        1.000 0.0    1   1   4         4         
9        1.000 0.0    1   1   2         2         
10       1.000 0.0    1   1   2         2         
*ALL*    2.615 1.895  0   6   13        34        
======== ===== ====== === === ========= ==========

Slowest operations
------------------
======================= ========= ========= ======
operation               time_sec  memory_mb counts
======================= ========= ========= ======
reading exposure        0.022     0.0       1     
building riskinputs     0.021     0.0       1     
assoc_assets_sites      0.011     0.0       1     
reading site collection 2.325E-04 0.0       1     
======================= ========= ========= ======