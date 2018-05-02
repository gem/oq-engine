disaggregation with a complex logic tree
========================================

============== ===================
checksum32     1,766,748,636      
date           2018-04-30T11:23:03
engine_version 3.1.0-gitb0812f0   
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
source_model_1.xml 1      Stable Shallow Crust 5.00000      4           
source_model_2.xml 2      Active Shallow Crust 543          543         
source_model_2.xml 3      Stable Shallow Crust 5.00000      1           
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
1         SimpleFaultSource         543          0.00285   1.764E-04  60        30        0     
2         CharacteristicFaultSource 1            6.700E-05 2.384E-06  8         4         0     
========= ========================= ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
========================= ========= ======
source_class              calc_time counts
========================= ========= ======
CharacteristicFaultSource 6.700E-05 1     
SimpleFaultSource         0.00285   1     
========================= ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ======= ========= ======= =========
operation-duration mean    stddev  min       max     num_tasks
count_ruptures     0.00239 0.00107 6.475E-04 0.00483 23       
================== ======= ======= ========= ======= =========

Fastest task
------------
taskno=15, weight=141, duration=0 s, sources="1"

======== ======= ====== === === =
variable mean    stddev min max n
======== ======= ====== === === =
nsites   2.00000 NaN    2   2   1
weight   141     NaN    141 141 1
======== ======= ====== === === =

Slowest task
------------
taskno=11, weight=124, duration=0 s, sources="1"

======== ======= ====== ======= === =
variable mean    stddev min     max n
======== ======= ====== ======= === =
nsites   2.00000 0.0    2       2   4
weight   31      19     8.48528 50  4
======== ======= ====== ======= === =

Informational data
------------------
============== ================================================================================ ========
task           sent                                                                             received
count_ruptures sources=39.38 KB param=28.88 KB srcfilter=17.29 KB monitor=7.41 KB gsims=4.94 KB 8.05 KB 
============== ================================================================================ ========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total count_ruptures           0.05505   1.90625   23    
managing sources               0.03911   0.0       1     
reading composite source model 0.02582   0.0       1     
store source_info              0.00554   0.0       1     
unpickling count_ruptures      0.00126   0.0       23    
splitting sources              9.263E-04 0.0       1     
aggregate curves               5.553E-04 0.0       23    
reading site collection        3.016E-04 0.0       1     
saving probability maps        3.815E-05 0.0       1     
============================== ========= ========= ======