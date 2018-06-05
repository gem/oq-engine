SHARE OpenQuake Computational Settings
======================================

============== ===================
checksum32     1,220,765,868      
date           2018-06-05T06:39:19
engine_version 3.2.0-git65c4735   
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
s46       AreaSource         7,770        0.19342   0.09147    1.00000   370       0     
i17       ComplexFaultSource 33,383       0.0       0.00224    0.0       0         0     
i20       ComplexFaultSource 9,241        0.0       6.964E-04  0.0       0         0     
v1        AreaSource         42           0.0       0.00186    0.0       0         0     
v4        AreaSource         168          0.0       0.00524    0.0       0         0     
sh13      AreaSource         41,952       0.0       0.76507    0.0       0         0     
sh14      AreaSource         41,952       0.0       0.77011    0.0       0         0     
sh6       AreaSource         12,900       0.0       0.19914    0.0       0         0     
scr293    AreaSource         61,740       0.0       1.79615    0.0       0         0     
scr299    AreaSource         1,572        0.0       0.03038    0.0       0         0     
scr301    AreaSource         17,268       0.0       0.44614    0.0       0         0     
scr304    AreaSource         574          0.0       0.00898    0.0       0         0     
s13       AreaSource         12,726       0.0       0.13541    0.0       0         0     
s34       AreaSource         12,327       0.0       0.12215    0.0       0         0     
s35       AreaSource         12,327       0.0       0.12434    0.0       0         0     
s40       AreaSource         12,327       0.0       0.12316    0.0       0         0     
s70       AreaSource         17,871       0.0       0.19850    0.0       0         0     
s72       AreaSource         17,871       0.0       0.19758    0.0       0         0     
========= ================== ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
================== ========= ======
source_class       calc_time counts
================== ========= ======
AreaSource         0.19342   16    
ComplexFaultSource 0.0       2     
================== ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =========
operation-duration mean    stddev  min     max     num_tasks
RtreeFilter        0.14273 0.14071 0.05836 1.13822 60       
count_eff_ruptures 0.00800 0.00334 0.00270 0.01694 34       
================== ======= ======= ======= ======= =========

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
taskno=21, weight=92, duration=0 s, sources="s46"

======== ======= ========= ======= ======= ==
variable mean    stddev    min     max     n 
======== ======= ========= ======= ======= ==
nsites   1.00000 0.0       1       1       11
weight   8.40000 1.000E-06 8.40000 8.40000 11
======== ======= ========= ======= ======= ==

Data transfer
-------------
================== ================================================================================== ========
task               sent                                                                               received
RtreeFilter        srcs=3.55 MB monitor=20.33 KB srcfilter=17.4 KB                                    85.91 KB
count_eff_ruptures sources=136.86 KB param=39.21 KB gsims=12.88 KB monitor=11.72 KB srcfilter=8.33 KB 11.95 KB
================== ================================================================================== ========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
PSHACalculator.run             13        0.17578   1     
total prefilter                8.56374   4.94141   60    
reading composite source model 6.75852   0.17578   1     
splitting sources              5.02860   0.0       1     
managing sources               1.52919   0.0       1     
total count_eff_ruptures       0.27187   5.75781   34    
unpickling prefilter           0.02296   0.0       60    
store source_info              0.02058   0.0       1     
aggregate curves               0.01069   0.0       34    
unpickling count_eff_ruptures  0.00984   0.0       34    
reading site collection        0.00104   0.0       1     
saving probability maps        1.915E-04 0.0       1     
============================== ========= ========= ======