Event Based Risk from GMF
=========================

============== ===================
checksum32     4,081,447,500      
date           2018-10-05T03:04:30
engine_version 3.3.0-git48e9a474fd
============== ===================

num_sites = 3, num_levels = 10

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
======================== ================================================
Name                     File                                            
======================== ================================================
exposure                 `exposure_model_2.xml <exposure_model_2.xml>`_  
gmfs                     `gmfs_3_2IM.csv <gmfs_3_2IM.csv>`_              
job_ini                  `job.ini <job.ini>`_                            
sites                    `sitemesh.csv <sitemesh.csv>`_                  
structural_vulnerability `vulnerability_2IM.xml <vulnerability_2IM.xml>`_
======================== ================================================

Composite source model
----------------------
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
b_1       1.00000 trivial(1)      1/1             
========= ======= =============== ================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)
  0,FromFile: [0]>

Number of ruptures per tectonic region type
-------------------------------------------
============ ====== === ============ ============
source_model grp_id trt eff_ruptures tot_ruptures
============ ====== === ============ ============
scenario     0      *   1            0           
============ ====== === ============ ============

Estimated data transfer for the avglosses
-----------------------------------------
3 asset(s) x 1 realization(s) x 1 loss type(s) x 1 losses x 8 bytes x 60 tasks = 1.41 KB

Exposure model
--------------
=============== ========
#assets         3       
#taxonomies     2       
deductibile     absolute
insurance_limit absolute
=============== ========

======== ======= ====== === === ========= ==========
taxonomy mean    stddev min max num_sites num_assets
RM       1.00000 0.0    1   1   2         2         
RC       1.00000 NaN    1   1   1         1         
*ALL*    1.00000 0.0    1   1   3         3         
======== ======= ====== === === ========= ==========

Slowest operations
------------------
================ ========= ========= ======
operation        time_sec  memory_mb counts
================ ========= ========= ======
reading exposure 5.965E-04 0.0       1     
================ ========= ========= ======