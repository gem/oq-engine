SHARE OpenQuake Computational Settings
======================================

============== ===================
checksum32     1,220,765,868      
date           2018-09-05T10:04:54
engine_version 3.2.0-gitb4ef3a4b6c
============== ===================

num_sites = 1, num_levels = 78

Parameters
----------
=============================== ===========================================
calculation_mode                'classical'                                
number_of_logic_tree_samples    0                                          
maximum_distance                {'default': [(6, 100), (7, 150), (9, 200)]}
investigation_time              50.0                                       
ses_per_logic_tree_path         1                                          
truncation_level                3.0                                        
rupture_mesh_spacing            5.0                                        
complex_fault_mesh_spacing      5.0                                        
width_of_mfd_bin                0.2                                        
area_source_discretization      10.0                                       
ground_motion_correlation_model None                                       
minimum_intensity               {}                                         
random_seed                     23                                         
master_seed                     0                                          
ses_seed                        42                                         
=============================== ===========================================

Input files
-----------
======================= ==========================================================================
Name                    File                                                                      
======================= ==========================================================================
gsim_logic_tree         `complete_gmpe_logic_tree.xml <complete_gmpe_logic_tree.xml>`_            
job_ini                 `job.ini <job.ini>`_                                                      
source                  `simple_area_source_model.xml <simple_area_source_model.xml>`_            
source_model_logic_tree `simple_source_model_logic_tree.xml <simple_source_model_logic_tree.xml>`_
======================= ==========================================================================

Composite source model
----------------------
========= ======= ====================== ================
smlt_path weight  gsim_logic_tree        num_realizations
========= ======= ====================== ================
b1        1.00000 complex(0,5,2,4,4,1,0) 4/160           
========= ======= ====================== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================================================================================================ ================= ======================= =================
grp_id gsims                                                                                            distances         siteparams              ruptparams       
====== ================================================================================================ ================= ======================= =================
0      AtkinsonBoore2003SInter() LinLee2008SInter() YoungsEtAl1997SInter() ZhaoEtAl2006SInter()         rhypo rrup        vs30                    hypo_depth mag   
1      FaccioliEtAl2010()                                                                               rrup              vs30                    mag rake         
2      Campbell2003SHARE() ToroEtAl2002SHARE()                                                          rjb rrup                                  mag rake         
3      AkkarBommer2010() Campbell2003SHARE() CauzziFaccioli2008() ChiouYoungs2008() ToroEtAl2002SHARE() rhypo rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
4      AtkinsonBoore2003SSlab() LinLee2008SSlab() YoungsEtAl1997SSlab() ZhaoEtAl2006SSlab()             rhypo rrup        vs30                    hypo_depth mag   
====== ================================================================================================ ================= ======================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=4, rlzs=4)
  4,AtkinsonBoore2003SSlab(): [0]
  4,LinLee2008SSlab(): [1]
  4,YoungsEtAl1997SSlab(): [2]
  4,ZhaoEtAl2006SSlab(): [3]>

Number of ruptures per tectonic region type
-------------------------------------------
============================ ====== ================= ============ ============
source_model                 grp_id trt               eff_ruptures tot_ruptures
============================ ====== ================= ============ ============
simple_area_source_model.xml 4      Subduction Inslab 7,770        93,219      
============================ ====== ================= ============ ============

Slowest sources
---------------
========= ================== ============ ========= ========== ========= ========= ======
source_id source_class       num_ruptures calc_time split_time num_sites num_split events
========= ================== ============ ========= ========== ========= ========= ======
s46       AreaSource         7,770        0.11524   0.08716    1.00000   370       0     
i17       ComplexFaultSource 33,383       0.0       0.00227    0.0       0         0     
i20       ComplexFaultSource 9,241        0.0       6.814E-04  0.0       0         0     
v1        AreaSource         42           0.0       0.00178    0.0       0         0     
v4        AreaSource         168          0.0       0.00525    0.0       0         0     
sh13      AreaSource         41,952       0.0       0.73617    0.0       0         0     
sh14      AreaSource         41,952       0.0       0.73711    0.0       0         0     
sh6       AreaSource         12,900       0.0       0.19189    0.0       0         0     
scr293    AreaSource         61,740       0.0       1.70149    0.0       0         0     
scr299    AreaSource         1,572        0.0       0.02881    0.0       0         0     
scr301    AreaSource         17,268       0.0       0.43138    0.0       0         0     
scr304    AreaSource         574          0.0       0.00819    0.0       0         0     
s13       AreaSource         12,726       0.0       0.16748    0.0       0         0     
s34       AreaSource         12,327       0.0       0.11732    0.0       0         0     
s35       AreaSource         12,327       0.0       0.11772    0.0       0         0     
s40       AreaSource         12,327       0.0       0.11594    0.0       0         0     
s70       AreaSource         17,871       0.0       0.19404    0.0       0         0     
s72       AreaSource         17,871       0.0       0.18990    0.0       0         0     
========= ================== ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
================== ========= ======
source_class       calc_time counts
================== ========= ======
AreaSource         0.11524   16    
ComplexFaultSource 0.0       2     
================== ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
==================== ======= ======= ======= ======= =========
operation-duration   mean    stddev  min     max     num_tasks
pickle_source_models 6.12540 NaN     6.12540 6.12540 1        
count_eff_ruptures   0.00432 0.00105 0.00245 0.00599 34       
preprocess           0.22011 0.11249 0.01673 0.50762 35       
==================== ======= ======= ======= ======= =========

Fastest task
------------
taskno=32, weight=92, duration=0 s, sources="s46"

======== ======= ========= ======= ======= ==
variable mean    stddev    min     max     n 
======== ======= ========= ======= ======= ==
nsites   1.00000 0.0       1       1       11
weight   8.40000 1.000E-06 8.40000 8.40000 11
======== ======= ========= ======= ======= ==

Slowest task
------------
taskno=4, weight=92, duration=0 s, sources="s46"

======== ======= ========= ======= ======= ==
variable mean    stddev    min     max     n 
======== ======= ========= ======= ======= ==
nsites   1.00000 0.0       1       1       11
weight   8.40000 1.000E-06 8.40000 8.40000 11
======== ======= ========= ======= ======= ==

Data transfer
-------------
==================== ================================================================================ ========
task                 sent                                                                             received
pickle_source_models monitor=0 B fnames=0 B converter=0 B                                             180 B   
count_eff_ruptures   sources=127.07 KB param=41.7 KB gsims=12.88 KB monitor=10.19 KB srcfilter=7.9 KB 11.95 KB
preprocess           srcs=3.63 MB monitor=10.9 KB srcfilter=9.26 KB param=1.23 KB                     84.16 KB
==================== ================================================================================ ========

Slowest operations
------------------
========================== ======== ========= ======
operation                  time_sec memory_mb counts
========================== ======== ========= ======
total preprocess           7.70392  0.05859   35    
total pickle_source_models 6.12540  0.0       1     
splitting sources          4.84614  0.0       1     
managing sources           0.71586  0.0       1     
total count_eff_ruptures   0.14692  0.0       34    
store source_info          0.01532  0.0       1     
aggregate curves           0.00699  0.0       34    
========================== ======== ========= ======