Event Based Risk SJ
===================

============== ===================
checksum32     771,335,712        
date           2018-02-19T09:59:45
engine_version 2.9.0-gitb536198   
============== ===================

num_sites = 61, num_levels = 1

Parameters
----------
=============================== =================
calculation_mode                'event_based'    
number_of_logic_tree_samples    0                
maximum_distance                {'default': 50.0}
investigation_time              25.0             
ses_per_logic_tree_path         1                
truncation_level                3.0              
rupture_mesh_spacing            5.0              
complex_fault_mesh_spacing      5.0              
width_of_mfd_bin                0.3              
area_source_discretization      10.0             
ground_motion_correlation_model 'JB2009'         
random_seed                     23               
master_seed                     0                
=============================== =================

Input files
-----------
======================= ====================================================================
Name                    File                                                                
======================= ====================================================================
gsim_logic_tree         `Costa_Rica_RESIS_II_gmpe_CQ.xml <Costa_Rica_RESIS_II_gmpe_CQ.xml>`_
job_ini                 `job.ini <job.ini>`_                                                
site_model              `site_model_CR_60.xml <site_model_CR_60.xml>`_                      
source                  `areasource.xml <areasource.xml>`_                                  
source_model_logic_tree `sm_lt.xml <sm_lt.xml>`_                                            
======================= ====================================================================

Composite source model
----------------------
========= ====== =============== ================
smlt_path weight gsim_logic_tree num_realizations
========= ====== =============== ================
b1        1.000  trivial(0,1,0)  1/1             
========= ====== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================= ========= ========== ===================
grp_id gsims             distances siteparams ruptparams         
====== ================= ========= ========== ===================
0      ZhaoEtAl2006Asc() rrup      vs30       hypo_depth mag rake
====== ================= ========= ========== ===================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)
  0,ZhaoEtAl2006Asc(): [0]>

Number of ruptures per tectonic region type
-------------------------------------------
============== ====== ==================== ============ ============
source_model   grp_id trt                  eff_ruptures tot_ruptures
============== ====== ==================== ============ ============
areasource.xml 0      Active Shallow Crust 516          516         
============== ====== ==================== ============ ============

Informational data
------------------
========================= ==================================================================================
compute_ruptures.received tot 63.28 KB, max_per_task 3.15 KB                                                
compute_ruptures.sent     src_filter 333 KB, sources 121 KB, param 47.28 KB, monitor 26.79 KB, gsims 9.99 KB
hazard.input_weight       51.6                                                                              
hazard.n_imts             1                                                                                 
hazard.n_levels           1                                                                                 
hazard.n_realizations     1                                                                                 
hazard.n_sites            61                                                                                
hazard.n_sources          1                                                                                 
hazard.output_weight      15.25                                                                             
hostname                  tstation.gem.lan                                                                  
require_epsilons          False                                                                             
========================= ==================================================================================

Slowest sources
---------------
========= ============ ============ ========= ========= =========
source_id source_class num_ruptures calc_time num_sites num_split
========= ============ ============ ========= ========= =========
1         AreaSource   516          0.0       1         0        
========= ============ ============ ========= ========= =========

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
AreaSource   0.0       1     
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
compute_ruptures   0.004 0.001  0.003 0.007 86       
================== ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ======== ========= ======
operation                      time_sec memory_mb counts
============================== ======== ========= ======
total compute_ruptures         0.371    0.121     86    
managing sources               0.284    0.0       1     
reading composite source model 0.029    0.0       1     
saving ruptures                0.005    0.0       86    
reading site collection        0.004    0.0       1     
store source_info              0.003    0.0       1     
making contexts                0.002    0.0       2     
setting event years            0.001    0.0       1     
============================== ======== ========= ======