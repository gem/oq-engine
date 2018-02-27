Event Based Risk QA Test 2
==========================

============== ===================
checksum32     3,754,416,453      
date           2018-02-25T06:42:03
engine_version 2.10.0-git1f7c0c0  
============== ===================

num_sites = 3, num_levels = 15

Parameters
----------
=============================== ==================
calculation_mode                'event_based_risk'
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 100.0}
investigation_time              50.0              
ses_per_logic_tree_path         20                
truncation_level                3.0               
rupture_mesh_spacing            5.0               
complex_fault_mesh_spacing      5.0               
width_of_mfd_bin                0.3               
area_source_discretization      10.0              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     23                
master_seed                     42                
ses_seed                        42                
avg_losses                      True              
=============================== ==================

Input files
-----------
======================== ==============================================================
Name                     File                                                          
======================== ==============================================================
exposure                 `exposure.xml <exposure.xml>`_                                
gsim_logic_tree          `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                  
job_ini                  `job.ini <job.ini>`_                                          
source                   `source_model.xml <source_model.xml>`_                        
source_model_logic_tree  `source_model_logic_tree.xml <source_model_logic_tree.xml>`_  
structural_vulnerability `vulnerability_model_stco.xml <vulnerability_model_stco.xml>`_
======================== ==============================================================

Composite source model
----------------------
========= ====== =============== ================
smlt_path weight gsim_logic_tree num_realizations
========= ====== =============== ================
b1        1.000  trivial(1)      1/1             
========= ====== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================= =========== ======================= =================
grp_id gsims             distances   siteparams              ruptparams       
====== ================= =========== ======================= =================
0      ChiouYoungs2008() rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
====== ================= =========== ======================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)
  0,ChiouYoungs2008(): [0]>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== ============ ============
source_model     grp_id trt                  eff_ruptures tot_ruptures
================ ====== ==================== ============ ============
source_model.xml 0      Active Shallow Crust 18           18          
================ ====== ==================== ============ ============

Informational data
------------------
========================= =============================================================================
compute_ruptures.received tot 16.13 KB, max_per_task 5.4 KB                                            
compute_ruptures.sent     sources 4.04 KB, src_filter 2.43 KB, param 2.4 KB, monitor 990 B, gsims 381 B
hazard.input_weight       1.8000000000000003                                                           
hazard.n_imts             3                                                                            
hazard.n_levels           15                                                                           
hazard.n_realizations     1                                                                            
hazard.n_sites            3                                                                            
hazard.n_sources          3                                                                            
hazard.output_weight      45.0                                                                         
hostname                  tstation.gem.lan                                                             
require_epsilons          True                                                                         
========================= =============================================================================

Estimated data transfer for the avglosses
-----------------------------------------
4 asset(s) x 1 realization(s) x 1 loss type(s) x 2 losses x 8 bytes x 20 tasks = 1.25 KB

Exposure model
--------------
=============== ========
#assets         4       
#taxonomies     3       
deductibile     absolute
insurance_limit absolute
=============== ========

======== ===== ====== === === ========= ==========
taxonomy mean  stddev min max num_sites num_assets
RM       1.000 0.0    1   1   2         2         
RC+      1.000 NaN    1   1   1         1         
W/1      1.000 NaN    1   1   1         1         
*ALL*    1.333 0.577  1   2   3         4         
======== ===== ====== === === ========= ==========

Slowest sources
---------------
========= ============ ============ ========= ========= =========
source_id source_class num_ruptures calc_time num_sites num_split
========= ============ ============ ========= ========= =========
3         PointSource  6            0.0       1         0        
1         PointSource  6            0.0       1         0        
2         PointSource  6            0.0       1         0        
========= ============ ============ ========= ========= =========

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
PointSource  0.0       3     
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ===== ========= ===== ===== =========
operation-duration mean  stddev    min   max   num_tasks
compute_ruptures   0.013 4.786E-04 0.012 0.013 3        
================== ===== ========= ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total compute_ruptures         0.039     0.602     3     
managing sources               0.033     0.0       1     
making contexts                0.012     0.0       9     
saving ruptures                0.006     0.0       3     
store source_info              0.003     0.0       1     
reading composite source model 0.002     0.0       1     
reading exposure               0.002     0.0       1     
setting event years            0.001     0.0       1     
reading site collection        5.007E-05 0.0       1     
============================== ========= ========= ======