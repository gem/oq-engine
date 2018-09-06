Classical PSHA QA test
======================

============== ===================
checksum32     2,024,827,974      
date           2018-09-05T10:04:38
engine_version 3.2.0-gitb4ef3a4b6c
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
1_0       CharacteristicFaultSource 11           0.00731   7.153E-07  11        2         0     
41_1      CharacteristicFaultSource 11           0.00679   9.537E-07  10        2         0     
47_0      CharacteristicFaultSource 11           0.00655   7.153E-07  8.00000   2         0     
4_1       CharacteristicFaultSource 11           0.00550   9.537E-07  12        2         0     
14_1      CharacteristicFaultSource 11           0.00460   4.768E-07  13        2         0     
11_1      CharacteristicFaultSource 11           0.00456   7.153E-07  16        1         0     
66_0      CharacteristicFaultSource 11           0.00455   7.153E-07  13        2         0     
2_1       CharacteristicFaultSource 11           0.00449   7.153E-07  11        2         0     
34_0      CharacteristicFaultSource 11           0.00447   7.153E-07  16        2         0     
38_1      CharacteristicFaultSource 11           0.00446   7.153E-07  10        2         0     
44_1      CharacteristicFaultSource 11           0.00444   7.153E-07  16        2         0     
36_0      CharacteristicFaultSource 11           0.00443   7.153E-07  13        2         0     
32_0      CharacteristicFaultSource 11           0.00439   7.153E-07  15        2         0     
52_0      CharacteristicFaultSource 11           0.00433   7.153E-07  12        2         0     
74_0      CharacteristicFaultSource 11           0.00418   7.153E-07  16        2         0     
0_0       CharacteristicFaultSource 11           0.00417   2.384E-06  9.66667   3         0     
24_0      CharacteristicFaultSource 11           0.00416   7.153E-07  4.50000   2         0     
27_1      CharacteristicFaultSource 11           0.00407   7.153E-07  11        2         0     
63_1      CharacteristicFaultSource 11           0.00347   7.153E-07  18        1         0     
70_0      CharacteristicFaultSource 11           0.00345   7.153E-07  17        2         0     
========= ========================= ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
========================= ========= ======
source_class              calc_time counts
========================= ========= ======
CharacteristicFaultSource 0.18750   246   
========================= ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
==================== ======= ======= ========= ======= =========
operation-duration   mean    stddev  min       max     num_tasks
pickle_source_models 1.43190 0.47279 1.09759   1.76621 2        
count_eff_ruptures   0.00357 0.00141 0.00186   0.00705 66       
preprocess           0.00299 0.00132 8.514E-04 0.00615 62       
==================== ======= ======= ========= ======= =========

Fastest task
------------
taskno=27, weight=461, duration=0 s, sources="76_0 76_1 77_0 77_1 78_0"

======== ==== ======= === === =
variable mean stddev  min max n
======== ==== ======= === === =
nsites   18   6.26099 7   21  5
weight   92   19      58  100 5
======== ==== ======= === === =

Slowest task
------------
taskno=4, weight=460, duration=0 s, sources="1_0 1_1 20_0 20_1 21_0 21_1 22_0 22_1 23_0 23_1"

======== ======= ======= === === ==
variable mean    stddev  min max n 
======== ======= ======= === === ==
nsites   5.00000 3.52767 1   9   10
weight   46      18      22  66  10
======== ======= ======= === === ==

Data transfer
-------------
==================== ================================================================================= ========
task                 sent                                                                              received
pickle_source_models monitor=618 B converter=578 B fnames=384 B                                        352 B   
count_eff_ruptures   sources=1.46 MB param=49.24 KB monitor=19.79 KB srcfilter=14.18 KB gsims=14.18 KB 45.05 KB
preprocess           srcs=1.51 MB monitor=19.31 KB srcfilter=15.32 KB param=2.18 KB                    1.44 MB 
==================== ================================================================================= ========

Slowest operations
------------------
========================== ======== ========= ======
operation                  time_sec memory_mb counts
========================== ======== ========= ======
total pickle_source_models 2.86380  0.64844   2     
managing sources           0.28335  0.0       1     
total count_eff_ruptures   0.23570  0.0       66    
total preprocess           0.18519  0.43750   62    
aggregate curves           0.01409  0.0       66    
store source_info          0.00757  0.0       1     
splitting sources          0.00299  0.0       1     
========================== ======== ========= ======