SHARE OpenQuake Computational Settings
======================================

============== ===================
checksum32     1,220,765,868      
date           2018-05-15T04:13:36
engine_version 3.1.0-git0acbc11   
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
====== ==================================================================================== ============== ========== ==============
grp_id gsims                                                                                distances      siteparams ruptparams    
====== ==================================================================================== ============== ========== ==============
4      AtkinsonBoore2003SSlab() LinLee2008SSlab() YoungsEtAl1997SSlab() ZhaoEtAl2006SSlab() rhypo rjb rrup vs30       hypo_depth mag
====== ==================================================================================== ============== ========== ==============

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
s46       AreaSource         7,770        0.00619   0.09082    370       370       0     
i17       ComplexFaultSource 33,383       0.0       0.00200    0         0         0     
i20       ComplexFaultSource 9,241        0.0       7.007E-04  0         0         0     
v1        AreaSource         42           0.0       0.00201    0         0         0     
v4        AreaSource         168          0.0       0.00541    0         0         0     
sh13      AreaSource         41,952       0.0       0.78898    0         0         0     
sh14      AreaSource         41,952       0.0       0.78446    0         0         0     
sh6       AreaSource         12,900       0.0       0.19663    0         0         0     
scr293    AreaSource         61,740       0.0       1.81797    0         0         0     
scr299    AreaSource         1,572        0.0       0.03044    0         0         0     
scr301    AreaSource         17,268       0.0       0.46800    0         0         0     
scr304    AreaSource         574          0.0       0.00889    0         0         0     
s13       AreaSource         12,726       0.0       0.13919    0         0         0     
s34       AreaSource         12,327       0.0       0.12364    0         0         0     
s35       AreaSource         12,327       0.0       0.12563    0         0         0     
s40       AreaSource         12,327       0.0       0.12407    0         0         0     
s70       AreaSource         17,871       0.0       0.20080    0         0         0     
s72       AreaSource         17,871       0.0       0.20194    0         0         0     
========= ================== ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
================== ========= ======
source_class       calc_time counts
================== ========= ======
AreaSource         0.00619   16    
ComplexFaultSource 0.0       2     
================== ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ========= ========= ======= =========
operation-duration mean    stddev    min       max     num_tasks
prefilter          0.14030 0.13438   0.06181   1.07302 60       
count_ruptures     0.00184 7.328E-04 7.298E-04 0.00336 34       
================== ======= ========= ========= ======= =========

Fastest task
------------
taskno=34, weight=58, duration=0 s, sources="s46"

======== ======= ========= ======= ======= =
variable mean    stddev    min     max     n
======== ======= ========= ======= ======= =
nsites   1.00000 0.0       1       1       7
weight   8.40000 1.030E-06 8.40000 8.40000 7
======== ======= ========= ======= ======= =

Slowest task
------------
taskno=8, weight=92, duration=0 s, sources="s46"

======== ======= ========= ======= ======= ==
variable mean    stddev    min     max     n 
======== ======= ========= ======= ======= ==
nsites   1.00000 0.0       1       1       11
weight   8.40000 1.000E-06 8.40000 8.40000 11
======== ======= ========= ======= ======= ==

Informational data
------------------
============== ================================================================================== ========
task           sent                                                                               received
prefilter      srcs=3.55 MB monitor=19.16 KB srcfilter=14.47 KB                                   85.91 KB
count_ruptures sources=136.86 KB param=38.58 KB srcfilter=24.4 KB gsims=12.88 KB monitor=11.06 KB 11.95 KB
============== ================================================================================== ========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total prefilter                8.41803   4.63672   60    
reading composite source model 6.73057   0.0       1     
splitting sources              5.12198   0.0       1     
managing sources               1.30785   0.0       1     
total count_ruptures           0.06270   0.00391   34    
store source_info              0.01504   0.0       1     
unpickling prefilter           0.00404   0.0       60    
unpickling count_ruptures      0.00103   0.0       34    
aggregate curves               4.513E-04 0.0       34    
reading site collection        2.854E-04 0.0       1     
saving probability maps        2.718E-05 0.0       1     
============================== ========= ========= ======