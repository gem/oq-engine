Event Based Risk SJ
===================

============== ===================
checksum32     771,335,712        
date           2018-03-26T15:56:45
engine_version 2.10.0-git543cfb0  
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
minimum_intensity               {}               
random_seed                     23               
master_seed                     0                
ses_seed                        42               
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

Slowest sources
---------------
========= ============ ============ ========= ========== ========= =========
source_id source_class num_ruptures calc_time split_time num_sites num_split
========= ============ ============ ========= ========== ========= =========
1         AreaSource   516          0.0       0.023      0         0        
========= ============ ============ ========= ========== ========= =========

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
compute_ruptures   0.217 NaN    0.217 0.217 1        
================== ===== ====== ===== ===== =========

Informational data
------------------
================ ========================================================================= ========
task             sent                                                                      received
compute_ruptures sources=21.73 KB src_filter=3.87 KB param=563 B monitor=330 B gsims=119 B 4.65 KB 
================ ========================================================================= ========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
managing sources               0.257     0.0       1     
total compute_ruptures         0.217     2.953     1     
reading composite source model 0.056     0.0       1     
splitting sources              0.024     0.0       1     
reading site collection        0.012     0.0       1     
store source_info              0.007     0.0       1     
saving ruptures                0.007     0.0       1     
setting event years            0.002     0.0       1     
making contexts                0.002     0.0       2     
unpickling compute_ruptures    4.179E-04 0.0       1     
============================== ========= ========= ======