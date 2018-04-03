Event Based Risk from GMF
=========================

============== ===================
checksum32     692,252,974        
date           2018-03-26T15:56:34
engine_version 2.10.0-git543cfb0  
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
minimum_intensity               {}                
random_seed                     42                
master_seed                     0                 
ses_seed                        42                
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

==================================== ===== ====== === === ========= ==========
taxonomy                             mean  stddev min max num_sites num_assets
MCF/LWALL+DLO/HEX:1/YBET:1980-2010   1.000 0.0    1   1   2         2         
W+WLI/LWALL+DNO/HEX:1/YPRE:1980      1.333 0.577  1   2   3         4         
CR+PC/LWALL+DUC/HEX:1/YBET:1980-2010 1.200 0.447  1   2   5         6         
MCF/LWALL+DUC/HEX:2/YBET:1980-2010   1.500 0.577  1   2   4         6         
MATO/LN+DNO/HEX:1/Y99                1.500 0.707  1   2   2         3         
W+WLI/LWALL+DLO/HEX:1/YPRE:1980      1.000 0.0    1   1   3         3         
CR+PC/LWALL+DLO/HEX:1/YBET:1980-2010 1.000 0.0    1   1   2         2         
MCF/LWALL+DUC/HEX:1/YBET:1980-2010   1.000 0.0    1   1   4         4         
MR/LWALL+DUC/HEX:1/YBET:1980-2010    1.000 0.0    1   1   2         2         
MR/LWALL+DLO/HEX:1/YBET:1980-2010    1.000 0.0    1   1   2         2         
*ALL*                                2.615 1.895  0   6   13        34        
==================================== ===== ====== === === ========= ==========

Slowest operations
------------------
======================= ========= ========= ======
operation               time_sec  memory_mb counts
======================= ========= ========= ======
building riskinputs     0.034     0.0       1     
reading exposure        0.034     0.0       1     
reading site collection 2.403E-04 0.0       1     
======================= ========= ========= ======