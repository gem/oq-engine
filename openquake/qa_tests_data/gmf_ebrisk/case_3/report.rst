Event Based Risk from GMF
=========================

============== ===================
checksum32     3,795,250,863      
date           2017-12-21T06:52:04
engine_version 2.9.0-git98c8442   
============== ===================

num_sites = 11, num_imts = 2

Parameters
----------
=============================== ============
calculation_mode                'gmf_ebrisk'
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
=============================== ============

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
CR+PC/LWALL+DLO/HEX:1/YBET:1980-2010 1.000 0.0    1   1   2         2         
CR+PC/LWALL+DUC/HEX:1/YBET:1980-2010 1.200 0.447  1   2   5         6         
MATO/LN+DNO/HEX:1/Y99                1.500 0.707  1   2   2         3         
MCF/LWALL+DLO/HEX:1/YBET:1980-2010   1.000 0.0    1   1   2         2         
MCF/LWALL+DUC/HEX:1/YBET:1980-2010   1.000 0.0    1   1   4         4         
MCF/LWALL+DUC/HEX:2/YBET:1980-2010   1.500 0.577  1   2   4         6         
MR/LWALL+DLO/HEX:1/YBET:1980-2010    1.000 0.0    1   1   2         2         
MR/LWALL+DUC/HEX:1/YBET:1980-2010    1.000 0.0    1   1   2         2         
W+WLI/LWALL+DLO/HEX:1/YPRE:1980      1.000 0.0    1   1   3         3         
W+WLI/LWALL+DNO/HEX:1/YPRE:1980      1.333 0.577  1   2   3         4         
*ALL*                                2.615 1.895  0   6   13        34        
==================================== ===== ====== === === ========= ==========

Slowest operations
------------------
======================= ========= ========= ======
operation               time_sec  memory_mb counts
======================= ========= ========= ======
building riskinputs     0.036     0.0       1     
reading exposure        0.028     0.0       1     
assoc_assets_sites      0.019     0.0       1     
reading site collection 2.265E-04 0.0       1     
======================= ========= ========= ======