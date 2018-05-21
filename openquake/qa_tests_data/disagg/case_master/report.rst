disaggregation with a complex logic tree
========================================

============== ===================
checksum32     1,766,748,636      
date           2018-05-15T04:14:28
engine_version 3.1.0-git0acbc11   
============== ===================

num_sites = 2, num_levels = 102

Parameters
----------
=============================== =================
calculation_mode                'disaggregation' 
number_of_logic_tree_samples    0                
maximum_distance                {'default': 60.0}
investigation_time              50.0             
ses_per_logic_tree_path         1                
truncation_level                3.0              
rupture_mesh_spacing            2.0              
complex_fault_mesh_spacing      2.0              
width_of_mfd_bin                0.1              
area_source_discretization      10.0             
ground_motion_correlation_model None             
minimum_intensity               {}               
random_seed                     24               
master_seed                     0                
ses_seed                        42               
=============================== =================

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
b1        0.25000 complex(2,2)    4/4             
b2        0.75000 complex(2,2)    4/4             
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ===================================== =========== ======================= =================
grp_id gsims                                 distances   siteparams              ruptparams       
====== ===================================== =========== ======================= =================
0      BooreAtkinson2008() ChiouYoungs2008() rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
1      AkkarBommer2010() ChiouYoungs2008()   rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
2      BooreAtkinson2008() ChiouYoungs2008() rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
3      AkkarBommer2010() ChiouYoungs2008()   rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
====== ===================================== =========== ======================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=8, rlzs=8)
  0,BooreAtkinson2008(): [0 1]
  0,ChiouYoungs2008(): [2 3]
  1,AkkarBommer2010(): [0 2]
  1,ChiouYoungs2008(): [1 3]
  2,BooreAtkinson2008(): [4 5]
  2,ChiouYoungs2008(): [6 7]
  3,AkkarBommer2010(): [4 6]
  3,ChiouYoungs2008(): [5 7]>

Number of ruptures per tectonic region type
-------------------------------------------
================== ====== ==================== ============ ============
source_model       grp_id trt                  eff_ruptures tot_ruptures
================== ====== ==================== ============ ============
source_model_1.xml 0      Active Shallow Crust 543          543         
source_model_1.xml 1      Stable Shallow Crust 5            4           
source_model_2.xml 2      Active Shallow Crust 543          543         
source_model_2.xml 3      Stable Shallow Crust 5            1           
================== ====== ==================== ============ ============

============= =====
#TRT models   4    
#eff_ruptures 1,096
#tot_ruptures 1,091
#tot_weight   3,086
============= =====

Slowest sources
---------------
========= ========================= ============ ========= ========== ========= ========= ======
source_id source_class              num_ruptures calc_time split_time num_sites num_split events
========= ========================= ============ ========= ========== ========= ========= ======
1         SimpleFaultSource         543          0.00115   1.404E-04  60        30        0     
2         CharacteristicFaultSource 1            9.370E-05 2.384E-06  8         4         0     
========= ========================= ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
========================= ========= ======
source_class              calc_time counts
========================= ========= ======
CharacteristicFaultSource 9.370E-05 1     
SimpleFaultSource         0.00115   1     
========================= ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ========= ========= ======= =========
operation-duration mean    stddev    min       max     num_tasks
prefilter          0.00602 0.00217   0.00209   0.01029 32       
count_ruptures     0.00140 3.031E-04 8.976E-04 0.00198 25       
================== ======= ========= ========= ======= =========

Fastest task
------------
taskno=1, weight=186, duration=0 s, sources="1"

======== ======= ====== === === =
variable mean    stddev min max n
======== ======= ====== === === =
nsites   2.00000 NaN    2   2   1
weight   186     NaN    186 186 1
======== ======= ====== === === =

Slowest task
------------
taskno=8, weight=141, duration=0 s, sources="1"

======== ======= ====== === === =
variable mean    stddev min max n
======== ======= ====== === === =
nsites   2.00000 NaN    2   2   1
weight   141     NaN    141 141 1
======== ======= ====== === === =

Informational data
------------------
============== =============================================================================== ========
task           sent                                                                            received
prefilter      srcs=42.48 KB monitor=10.19 KB srcfilter=7.16 KB                                46.04 KB
count_ruptures sources=42.31 KB param=31.4 KB srcfilter=18.82 KB monitor=8.13 KB gsims=5.37 KB 8.75 KB 
============== =============================================================================== ========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total prefilter                0.19276   5.13281   32    
managing sources               0.12841   0.0       1     
total count_ruptures           0.03495   0.58594   25    
reading composite source model 0.02323   0.0       1     
store source_info              0.00538   0.0       1     
unpickling prefilter           0.00229   0.0       32    
unpickling count_ruptures      0.00134   0.0       25    
splitting sources              8.054E-04 0.0       1     
aggregate curves               5.848E-04 0.0       25    
reading site collection        2.480E-04 0.0       1     
saving probability maps        3.624E-05 0.0       1     
============================== ========= ========= ======