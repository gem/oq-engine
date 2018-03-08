QA test for blocksize independence (hazard)
===========================================

============== ===================
checksum32     1,989,351,768      
date           2018-02-25T06:43:38
engine_version 2.10.0-git1f7c0c0  
============== ===================

num_sites = 2, num_levels = 4

Parameters
----------
=============================== ==================
calculation_mode                'event_based'     
number_of_logic_tree_samples    1                 
maximum_distance                {'default': 400.0}
investigation_time              5.0               
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            10.0              
complex_fault_mesh_spacing      10.0              
width_of_mfd_bin                0.5               
area_source_discretization      10.0              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     42                
master_seed                     0                 
ses_seed                        1024              
=============================== ==================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
source                  `source_model.xml <source_model.xml>`_                      
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

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
source_model.xml 0      Active Shallow Crust 10,399       22,406      
================ ====== ==================== ============ ============

Informational data
------------------
========================= ====================================================================================
compute_ruptures.received tot 35.04 KB, max_per_task 5.38 KB                                                  
compute_ruptures.sent     sources 484.71 KB, src_filter 7.58 KB, param 5.76 KB, monitor 3.22 KB, gsims 1.24 KB
hazard.input_weight       2240.6                                                                              
hazard.n_imts             1                                                                                   
hazard.n_levels           4                                                                                   
hazard.n_realizations     1                                                                                   
hazard.n_sites            2                                                                                   
hazard.n_sources          9                                                                                   
hazard.output_weight      0.1                                                                                 
hostname                  tstation.gem.lan                                                                    
require_epsilons          False                                                                               
========================= ====================================================================================

Slowest sources
---------------
========= ============ ============ ========= ========= =========
source_id source_class num_ruptures calc_time num_sites num_split
========= ============ ============ ========= ========= =========
3         AreaSource   1,760        0.0       1         0        
9         AreaSource   897          0.0       1         0        
1         AreaSource   7,020        0.0       1         0        
2         AreaSource   2,334        0.0       1         0        
8         AreaSource   1,812        0.0       1         0        
6         AreaSource   1,270        0.0       1         0        
4         AreaSource   1,077        0.0       1         0        
5         AreaSource   2,092        0.0       1         0        
7         AreaSource   4,144        0.0       1         0        
========= ============ ============ ========= ========= =========

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
AreaSource   0.0       9     
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
compute_ruptures   0.470 0.143  0.185 0.652 10       
================== ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total compute_ruptures         4.698     0.0       10    
reading composite source model 2.991     0.0       1     
managing sources               2.722     0.0       1     
saving ruptures                0.011     0.0       10    
store source_info              0.004     0.0       1     
making contexts                0.002     0.0       3     
setting event years            0.001     0.0       1     
reading site collection        5.007E-05 0.0       1     
============================== ========= ========= ======