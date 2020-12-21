Event Based Risk from GMF
=========================

============== ====================
checksum32     648_091_558         
date           2020-11-02T09:35:30 
engine_version 3.11.0-git82b78631ac
============== ====================

num_sites = 13, num_levels = 2, num_rlzs = 1

Parameters
----------
=============================== ==================
calculation_mode                'event_based_risk'
number_of_logic_tree_samples    0                 
maximum_distance                None              
investigation_time              1.0               
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
====== ============ ====
grp_id gsim         rlzs
====== ============ ====
0      '[FromFile]' [0] 
====== ============ ====

Estimated data transfer for the avglosses
-----------------------------------------
120 asset(s) x 1 realization(s) x 1 loss type(s) losses x 8 bytes x 20 tasks = 18.75 KB

Exposure model
--------------
=========== ===
#assets     120
#taxonomies 10 
=========== ===

==================================== ========== ======= ====== === === =========
taxonomy                             num_assets mean    stddev min max num_sites
MCF/LWALL+DLO/HEX:1/YBET:1980-2010   7          1.57143 57%    1   3   11       
W+WLI/LWALL+DNO/HEX:1/YPRE:1980      5          2.20000 44%    1   4   11       
CR+PC/LWALL+DUC/HEX:1/YBET:1980-2010 10         1.60000 74%    1   5   16       
MCF/LWALL+DUC/HEX:2/YBET:1980-2010   8          1.62500 52%    1   3   13       
MATO/LN+DNO/HEX:1/Y99                11         1.54545 50%    1   3   17       
W+WLI/LWALL+DLO/HEX:1/YPRE:1980      7          2.00000 84%    1   6   14       
CR+PC/LWALL+DLO/HEX:1/YBET:1980-2010 4          2.25000 36%    1   3   9        
MCF/LWALL+DUC/HEX:1/YBET:1980-2010   6          2.00000 57%    1   4   12       
MR/LWALL+DUC/HEX:1/YBET:1980-2010    7          1.85714 53%    1   4   13       
MR/LWALL+DLO/HEX:1/YBET:1980-2010    4          1.00000 0%     1   1   4        
*ALL*                                13         9.23077 95%    2   36  120      
==================================== ========== ======= ====== === === =========

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
calc_47208       time_sec memory_mb counts
================ ======== ========= ======
importing inputs 0.05266  0.67578   1     
reading exposure 0.01030  0.01172   1     
================ ======== ========= ======