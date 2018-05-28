Classical PSHA QA test
======================

============== ===================
checksum32     2,024,827,974      
date           2018-05-15T04:13:07
engine_version 3.1.0-git0acbc11   
============== ===================

num_sites = 21, num_levels = 26

Parameters
----------
=============================== ==================
calculation_mode                'classical'       
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              50.0              
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            4.0               
complex_fault_mesh_spacing      4.0               
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
======================= ================================================================
Name                    File                                                            
======================= ================================================================
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                    
job_ini                 `job.ini <job.ini>`_                                            
sites                   `qa_sites.csv <qa_sites.csv>`_                                  
source                  `aFault_aPriori_D2.1.xml <aFault_aPriori_D2.1.xml>`_            
source                  `bFault_stitched_D2.1_Char.xml <bFault_stitched_D2.1_Char.xml>`_
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_    
======================= ================================================================

Composite source model
----------------------
========================= ======= =============== ================
smlt_path                 weight  gsim_logic_tree num_realizations
========================= ======= =============== ================
aFault_aPriori_D2.1       0.50000 simple(2)       2/2             
bFault_stitched_D2.1_Char 0.50000 simple(2)       2/2             
========================= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ===================================== =========== ======================= =================
grp_id gsims                                 distances   siteparams              ruptparams       
====== ===================================== =========== ======================= =================
0      BooreAtkinson2008() ChiouYoungs2008() rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
1      BooreAtkinson2008() ChiouYoungs2008() rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
====== ===================================== =========== ======================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=4, rlzs=4)
  0,BooreAtkinson2008(): [0]
  0,ChiouYoungs2008(): [1]
  1,BooreAtkinson2008(): [2]
  1,ChiouYoungs2008(): [3]>

Number of ruptures per tectonic region type
-------------------------------------------
============================= ====== ==================== ============ ============
source_model                  grp_id trt                  eff_ruptures tot_ruptures
============================= ====== ==================== ============ ============
aFault_aPriori_D2.1.xml       0      Active Shallow Crust 2,013        1,980       
bFault_stitched_D2.1_Char.xml 1      Active Shallow Crust 2,321        2,706       
============================= ====== ==================== ============ ============

============= ======
#TRT models   2     
#eff_ruptures 4,334 
#tot_ruptures 4,686 
#tot_weight   27,837
============= ======

Slowest sources
---------------
========= ========================= ============ ========= ========== ========= ========= ======
source_id source_class              num_ruptures calc_time split_time num_sites num_split events
========= ========================= ============ ========= ========== ========= ========= ======
35_1      CharacteristicFaultSource 11           1.969E-04 1.192E-06  27        2         0     
47_0      CharacteristicFaultSource 11           1.943E-04 9.537E-07  16        2         0     
57_0      CharacteristicFaultSource 11           1.726E-04 1.192E-06  23        2         0     
36_0      CharacteristicFaultSource 11           1.712E-04 9.537E-07  26        2         0     
44_1      CharacteristicFaultSource 11           1.590E-04 9.537E-07  33        2         0     
4_1       CharacteristicFaultSource 11           1.583E-04 9.537E-07  24        2         0     
42_0      CharacteristicFaultSource 11           1.433E-04 9.537E-07  19        2         0     
47_1      CharacteristicFaultSource 11           1.380E-04 1.192E-06  16        2         0     
2_1       CharacteristicFaultSource 11           1.378E-04 9.537E-07  23        2         0     
1_0       CharacteristicFaultSource 11           1.304E-04 1.192E-06  22        2         0     
72_0      CharacteristicFaultSource 11           1.264E-04 9.537E-07  31        2         0     
48_0      CharacteristicFaultSource 11           1.249E-04 9.537E-07  12        2         0     
81_1      CharacteristicFaultSource 11           1.249E-04 9.537E-07  14        2         0     
0_0       CharacteristicFaultSource 11           1.237E-04 1.669E-06  29        3         0     
57_1      CharacteristicFaultSource 11           1.223E-04 9.537E-07  23        2         0     
66_0      CharacteristicFaultSource 11           1.206E-04 9.537E-07  26        2         0     
34_0      CharacteristicFaultSource 11           1.197E-04 9.537E-07  32        2         0     
48_1      CharacteristicFaultSource 11           1.187E-04 1.192E-06  12        2         0     
41_1      CharacteristicFaultSource 11           1.159E-04 1.192E-06  21        2         0     
30_1      CharacteristicFaultSource 11           1.144E-04 9.537E-07  21        2         0     
========= ========================= ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
========================= ========= ======
source_class              calc_time counts
========================= ========= ======
CharacteristicFaultSource 0.01551   246   
========================= ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ========= ========= ======= =========
operation-duration mean    stddev    min       max     num_tasks
prefilter          0.00674 0.00366   0.00162   0.01553 54       
count_ruptures     0.00204 6.287E-04 9.575E-04 0.00372 66       
================== ======= ========= ========= ======= =========

Fastest task
------------
taskno=23, weight=401, duration=0 s, sources="68_1 69_0 69_1 6_0 6_1"

======== ==== ======= === === =
variable mean stddev  min max n
======== ==== ======= === === =
nsites   13   4.27785 9   18  5
weight   80   13      66  93  5
======== ==== ======= === === =

Slowest task
------------
taskno=53, weight=450, duration=0 s, sources="52_1 53_0 53_1 54_0 54_1 55_0 55_1 56_0 56_1 57_0"

======== ======= ======= === === ==
variable mean    stddev  min max n 
======== ======= ======= === === ==
nsites   4.30000 1.56702 3   8   10
weight   45      7.75760 38  62  10
======== ======= ======= === === ==

Informational data
------------------
============== ================================================================================== ========
task           sent                                                                               received
prefilter      srcs=1.53 MB monitor=17.19 KB srcfilter=12.08 KB                                   1.46 MB 
count_ruptures sources=1.48 MB srcfilter=116.02 KB param=43.18 KB monitor=21.46 KB gsims=14.18 KB 45.05 KB
============== ================================================================================== ========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
reading composite source model 2.93934   0.0       1     
total prefilter                0.36386   3.58594   54    
managing sources               0.30467   0.0       1     
total count_ruptures           0.13462   0.12500   66    
unpickling prefilter           0.02750   0.0       54    
store source_info              0.00689   0.0       1     
unpickling count_ruptures      0.00362   0.0       66    
aggregate curves               0.00225   0.0       66    
splitting sources              0.00201   0.0       1     
reading site collection        5.965E-04 0.0       1     
saving probability maps        3.386E-05 0.0       1     
============================== ========= ========= ======