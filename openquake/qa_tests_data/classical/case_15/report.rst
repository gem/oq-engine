Classical PSHA with GMPE logic tree with multiple tectonic region types
=======================================================================

============== ===================
checksum32     17,280,623         
date           2018-09-05T10:04:38
engine_version 3.2.0-gitb4ef3a4b6c
============== ===================

num_sites = 3, num_levels = 17

Parameters
----------
=============================== ==================
calculation_mode                'classical'       
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              50.0              
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            1.0               
complex_fault_mesh_spacing      1.0               
width_of_mfd_bin                0.1               
area_source_discretization      10.0              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     23                
master_seed                     0                 
ses_seed                        42                
=============================== ==================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
source                  `source_model_1.xml <source_model_1.xml>`_                  
source                  `source_model_2.xml <source_model_2.xml>`_                  
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
============== ======= =============== ================
smlt_path      weight  gsim_logic_tree num_realizations
============== ======= =============== ================
SM1            0.50000 complex(2,2)    4/4             
SM2_a3b1       0.25000 complex(2,2)    2/2             
SM2_a3pt2b0pt8 0.25000 complex(2,2)    2/2             
============== ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== =========================================== ========= ========== =================
grp_id gsims                                       distances siteparams ruptparams       
====== =========================================== ========= ========== =================
0      BooreAtkinson2008() CampbellBozorgnia2008() rjb rrup  vs30 z2pt5 dip mag rake ztor
1      Campbell2003() ToroEtAl2002()               rjb rrup             mag              
2      BooreAtkinson2008() CampbellBozorgnia2008() rjb rrup  vs30 z2pt5 dip mag rake ztor
3      BooreAtkinson2008() CampbellBozorgnia2008() rjb rrup  vs30 z2pt5 dip mag rake ztor
====== =========================================== ========= ========== =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=8, rlzs=8)
  0,BooreAtkinson2008(): [0 1]
  0,CampbellBozorgnia2008(): [2 3]
  1,Campbell2003(): [0 2]
  1,ToroEtAl2002(): [1 3]
  2,BooreAtkinson2008(): [4]
  2,CampbellBozorgnia2008(): [5]
  3,BooreAtkinson2008(): [6]
  3,CampbellBozorgnia2008(): [7]>

Number of ruptures per tectonic region type
-------------------------------------------
================== ====== ======================== ============ ============
source_model       grp_id trt                      eff_ruptures tot_ruptures
================== ====== ======================== ============ ============
source_model_1.xml 0      Active Shallow Crust     495          15          
source_model_1.xml 1      Stable Continental Crust 15           15          
source_model_2.xml 2      Active Shallow Crust     495          240         
source_model_2.xml 3      Active Shallow Crust     495          240         
================== ====== ======================== ============ ============

============= =====
#TRT models   4    
#eff_ruptures 1,500
#tot_ruptures 510  
#tot_weight   176  
============= =====

Slowest sources
---------------
========= ============ ============ ========= ========== ========= ========= ======
source_id source_class num_ruptures calc_time split_time num_sites num_split events
========= ============ ============ ========= ========== ========= ========= ======
1         AreaSource   240          0.00390   0.00266    3.00000   99        0     
2         PointSource  15           0.00293   1.431E-06  3.00000   1         0     
========= ============ ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
AreaSource   0.00390   1     
PointSource  0.00293   1     
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
==================== ======= ========= ========= ======= =========
operation-duration   mean    stddev    min       max     num_tasks
pickle_source_models 0.00582 0.00579   0.00172   0.00991 2        
count_eff_ruptures   0.00479 0.00170   0.00358   0.00599 2        
preprocess           0.00146 3.571E-04 6.580E-04 0.00200 34       
==================== ======= ========= ========= ======= =========

Fastest task
------------
taskno=2, weight=5, duration=0 s, sources="2"

======== ======= ====== ======= ======= =
variable mean    stddev min     max     n
======== ======= ====== ======= ======= =
nsites   3.00000 NaN    3       3       1
weight   5.19615 NaN    5.19615 5.19615 1
======== ======= ====== ======= ======= =

Slowest task
------------
taskno=1, weight=171, duration=0 s, sources="1"

======== ======= ====== ======= ======= ==
variable mean    stddev min     max     n 
======== ======= ====== ======= ======= ==
nsites   3.00000 0.0    3       3       33
weight   5.19615 0.0    5.19615 5.19615 33
======== ======= ====== ======= ======= ==

Data transfer
-------------
==================== ======================================================================== ========
task                 sent                                                                     received
pickle_source_models monitor=618 B converter=578 B fnames=368 B                               320 B   
count_eff_ruptures   sources=17.56 KB param=1.35 KB monitor=614 B srcfilter=440 B gsims=430 B 737 B   
preprocess           srcs=42.21 KB monitor=10.59 KB srcfilter=8.4 KB param=1.2 KB             44.15 KB
==================== ======================================================================== ========

Slowest operations
------------------
========================== ========= ========= ======
operation                  time_sec  memory_mb counts
========================== ========= ========= ======
managing sources           0.12813   0.0       1     
total preprocess           0.04968   0.12109   34    
total pickle_source_models 0.01163   0.18359   2     
total count_eff_ruptures   0.00957   0.0       2     
splitting sources          0.00655   0.0       1     
store source_info          0.00559   0.0       1     
aggregate curves           4.389E-04 0.0       2     
========================== ========= ========= ======