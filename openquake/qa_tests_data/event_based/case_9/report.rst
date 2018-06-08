Event Based Risk SJ
===================

============== ===================
checksum32     1,454,548,513      
date           2018-06-05T06:39:50
engine_version 3.2.0-git65c4735   
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
area_source_discretization      20.0             
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
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
b1        1.00000 trivial(1,0,0)  1/1             
========= ======= =============== ================

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
areasource.xml 0      Active Shallow Crust 120          120         
============== ====== ==================== ============ ============

Slowest sources
---------------
========= ============ ============ ========= ========== ========= ========= ======
source_id source_class num_ruptures calc_time split_time num_sites num_split events
========= ============ ============ ========= ========== ========= ========= ======
1         AreaSource   120          0.07130   0.00581    19        20        38    
========= ============ ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
AreaSource   0.07130   1     
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =========
operation-duration mean    stddev  min     max     num_tasks
RtreeFilter        0.00424 0.00136 0.00149 0.00578 20       
compute_ruptures   0.08072 NaN     0.08072 0.08072 1        
================== ======= ======= ======= ======= =========

Data transfer
-------------
================ ====================================================================== ========
task             sent                                                                   received
RtreeFilter      srcs=27.24 KB monitor=6.76 KB srcfilter=5.45 KB                        29.62 KB
compute_ruptures sources=13.2 KB param=576 B monitor=353 B src_filter=233 B gsims=119 B 5.63 KB 
================ ====================================================================== ========

Slowest operations
------------------
=============================== ========= ========= ======
operation                       time_sec  memory_mb counts
=============================== ========= ========= ======
EventBasedRuptureCalculator.run 0.60524   0.0       1     
managing sources                0.39321   0.0       1     
total prefilter                 0.08483   3.46875   20    
total compute_ruptures          0.08072   6.99609   1     
reading composite source model  0.01106   0.0       1     
saving ruptures                 0.00884   0.0       1     
store source_info               0.00844   0.0       1     
splitting sources               0.00618   0.0       1     
unpickling prefilter            0.00596   0.0       20    
reading site collection         0.00428   0.0       1     
setting event years             0.00220   0.0       1     
making contexts                 0.00155   0.0       3     
unpickling compute_ruptures     7.331E-04 0.0       1     
=============================== ========= ========= ======