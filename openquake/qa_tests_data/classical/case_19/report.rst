SHARE OpenQuake Computational Settings
======================================

============== ===================
checksum32     1,220,765,868      
date           2018-04-30T11:22:16
engine_version 3.1.0-gitb0812f0   
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
b1        1.00000 complex(0,5,2,4,4,1,0) 4/4             
========= ======= ====================== ================

Required parameters per tectonic region type
--------------------------------------------
====== ==================================================================================== ========== ========== ==============
grp_id gsims                                                                                distances  siteparams ruptparams    
====== ==================================================================================== ========== ========== ==============
4      AtkinsonBoore2003SSlab() LinLee2008SSlab() YoungsEtAl1997SSlab() ZhaoEtAl2006SSlab() rhypo rrup vs30       hypo_depth mag
====== ==================================================================================== ========== ========== ==============

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
s46       AreaSource         7,770        0.01712   0.08722    370       370       0     
i17       ComplexFaultSource 33,383       0.0       0.00207    0         0         0     
i20       ComplexFaultSource 9,241        0.0       7.904E-04  0         0         0     
v1        AreaSource         42           0.0       0.00177    0         0         0     
v4        AreaSource         168          0.0       0.00496    0         0         0     
sh13      AreaSource         41,952       0.0       0.73134    0         0         0     
sh14      AreaSource         41,952       0.0       0.75776    0         0         0     
sh6       AreaSource         12,900       0.0       0.19056    0         0         0     
scr293    AreaSource         61,740       0.0       1.70536    0         0         0     
scr299    AreaSource         1,572        0.0       0.02823    0         0         0     
scr301    AreaSource         17,268       0.0       0.43367    0         0         0     
scr304    AreaSource         574          0.0       0.00851    0         0         0     
s13       AreaSource         12,726       0.0       0.13122    0         0         0     
s34       AreaSource         12,327       0.0       0.11807    0         0         0     
s35       AreaSource         12,327       0.0       0.12530    0         0         0     
s40       AreaSource         12,327       0.0       0.12148    0         0         0     
s70       AreaSource         17,871       0.0       0.18995    0         0         0     
s72       AreaSource         17,871       0.0       0.19424    0         0         0     
========= ================== ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
================== ========= ======
source_class       calc_time counts
================== ========= ======
AreaSource         0.01712   16    
ComplexFaultSource 0.0       2     
================== ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ======= ========= ======= =========
operation-duration mean    stddev  min       max     num_tasks
count_ruptures     0.00376 0.00279 8.140E-04 0.01389 34       
================== ======= ======= ========= ======= =========

Fastest task
------------
taskno=16, weight=92, duration=0 s, sources="s46"

======== ======= ========= ======= ======= ==
variable mean    stddev    min     max     n 
======== ======= ========= ======= ======= ==
nsites   1.00000 0.0       1       1       11
weight   8.40000 1.000E-06 8.40000 8.40000 11
======== ======= ========= ======= ======= ==

Slowest task
------------
taskno=1, weight=92, duration=0 s, sources="s46"

======== ======= ========= ======= ======= ==
variable mean    stddev    min     max     n 
======== ======= ========= ======= ======= ==
nsites   1.00000 0.0       1       1       11
weight   8.40000 1.000E-06 8.40000 8.40000 11
======== ======= ========= ======= ======= ==

Informational data
------------------
============== =================================================================================== ========
task           sent                                                                                received
count_ruptures sources=126.83 KB param=38.58 KB srcfilter=24.37 KB gsims=12.88 KB monitor=10.96 KB 11.95 KB
============== =================================================================================== ========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
reading composite source model 6.42618   0.0       1     
splitting sources              4.84270   1.05859   1     
managing sources               3.65558   0.0       1     
total count_ruptures           0.12783   1.69531   34    
store source_info              0.01956   0.0       1     
unpickling count_ruptures      0.00186   0.0       34    
aggregate curves               8.187E-04 0.0       34    
reading site collection        3.028E-04 0.0       1     
saving probability maps        3.457E-05 0.0       1     
============================== ========= ========= ======