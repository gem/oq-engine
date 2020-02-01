Event Based Risk from GMF
=========================

============== ===================
checksum32     3_758_233_230      
date           2020-01-16T05:30:40
engine_version 3.8.0-git83c45f7244
============== ===================

num_sites = 13, num_levels = 170, num_rlzs = 1

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
pointsource_distance            None              
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
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
b_1       1.00000 trivial(1)      1               
========= ======= =============== ================

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)>

Estimated data transfer for the avglosses
-----------------------------------------
120 asset(s) x 1 realization(s) x 1 loss type(s) losses x 8 bytes x 20 tasks = 18.75 KB

Exposure model
--------------
=========== ===
#assets     120
#taxonomies 10 
=========== ===

==================================== ======= ======= === === ========= ==========
taxonomy                             mean    stddev  min max num_sites num_assets
MCF/LWALL+DLO/HEX:1/YBET:1980-2010   1.57143 0.97590 1   3   7         11        
W+WLI/LWALL+DNO/HEX:1/YPRE:1980      2.20000 1.09545 1   4   5         11        
CR+PC/LWALL+DUC/HEX:1/YBET:1980-2010 1.60000 1.26491 1   5   10        16        
MCF/LWALL+DUC/HEX:2/YBET:1980-2010   1.62500 0.91613 1   3   8         13        
MATO/LN+DNO/HEX:1/Y99                1.54545 0.82020 1   3   11        17        
W+WLI/LWALL+DLO/HEX:1/YPRE:1980      2.00000 1.82574 1   6   7         14        
CR+PC/LWALL+DLO/HEX:1/YBET:1980-2010 2.25000 0.95743 1   3   4         9         
MCF/LWALL+DUC/HEX:1/YBET:1980-2010   2.00000 1.26491 1   4   6         12        
MR/LWALL+DUC/HEX:1/YBET:1980-2010    1.85714 1.06904 1   4   7         13        
MR/LWALL+DLO/HEX:1/YBET:1980-2010    1.00000 0.0     1   1   4         4         
*ALL*                                9.23077 9.16655 2   36  13        120       
==================================== ======= ======= === === ========= ==========

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
================ ======== ========= ======
calc_43194       time_sec memory_mb counts
================ ======== ========= ======
reading exposure 0.00859  0.0       1     
================ ======== ========= ======