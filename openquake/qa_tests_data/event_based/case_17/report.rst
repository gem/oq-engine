Event Based Hazard QA Test, Case 17
===================================

============== ===================
checksum32     1,674,094,073      
date           2018-06-05T06:39:40
engine_version 3.2.0-git65c4735   
============== ===================

num_sites = 1, num_levels = 3

Parameters
----------
=============================== ==================
calculation_mode                'event_based'     
number_of_logic_tree_samples    5                 
maximum_distance                {'default': 200.0}
investigation_time              1.0               
ses_per_logic_tree_path         3                 
truncation_level                2.0               
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                1.0               
area_source_discretization      20.0              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     106               
master_seed                     0                 
ses_seed                        106               
=============================== ==================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gsim_logic_tree.xml <gsim_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
source                  `source_model_1.xml <source_model_1.xml>`_                  
source                  `source_model_2.xml <source_model_2.xml>`_                  
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
b1        0.20000 trivial(1)      3/1             
b2        0.20000 trivial(1)      2/1             
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================ ========= ========== ==========
grp_id gsims            distances siteparams ruptparams
====== ================ ========= ========== ==========
0      SadighEtAl1997() rrup      vs30       mag rake  
1      SadighEtAl1997() rrup      vs30       mag rake  
====== ================ ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=2, rlzs=5)
  0,SadighEtAl1997(): [0 1 2]
  1,SadighEtAl1997(): [3 4]>

Number of ruptures per tectonic region type
-------------------------------------------
================== ====== ==================== ============ ============
source_model       grp_id trt                  eff_ruptures tot_ruptures
================== ====== ==================== ============ ============
source_model_1.xml 0      Active Shallow Crust 39           39          
source_model_2.xml 1      Active Shallow Crust 7            7           
================== ====== ==================== ============ ============

============= ==
#TRT models   2 
#eff_ruptures 46
#tot_ruptures 46
#tot_weight   0 
============= ==

Slowest sources
---------------
========= ============ ============ ========= ========== ========= ========= ======
source_id source_class num_ruptures calc_time split_time num_sites num_split events
========= ============ ============ ========= ========== ========= ========= ======
1         PointSource  39           0.02343   8.106E-06  1.00000   1         0     
2         PointSource  7            0.00592   1.669E-06  1.00000   1         13    
========= ============ ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
PointSource  0.02935   2     
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ========= ======= ======= =========
operation-duration mean    stddev    min     max     num_tasks
RtreeFilter        0.00256 4.248E-05 0.00253 0.00259 2        
compute_ruptures   0.02095 0.01236   0.01221 0.02969 2        
================== ======= ========= ======= ======= =========

Data transfer
-------------
================ ======================================================================= ========
task             sent                                                                    received
RtreeFilter      srcs=2.99 KB monitor=692 B srcfilter=558 B                              3.08 KB 
compute_ruptures sources=3.2 KB param=1.16 KB monitor=706 B src_filter=466 B gsims=240 B 4.3 KB  
================ ======================================================================= ========

Slowest operations
------------------
=============================== ========= ========= ======
operation                       time_sec  memory_mb counts
=============================== ========= ========= ======
EventBasedRuptureCalculator.run 0.40746   0.0       1     
managing sources                0.24139   0.0       1     
total compute_ruptures          0.04190   6.99609   2     
saving ruptures                 0.00831   0.0       2     
store source_info               0.00789   0.0       1     
reading composite source model  0.00605   0.0       1     
total prefilter                 0.00512   2.22656   2     
setting event years             0.00212   0.0       1     
unpickling compute_ruptures     0.00148   0.0       2     
making contexts                 0.00109   0.0       3     
reading site collection         8.724E-04 0.0       1     
unpickling prefilter            5.765E-04 0.0       2     
splitting sources               3.469E-04 0.0       1     
=============================== ========= ========= ======