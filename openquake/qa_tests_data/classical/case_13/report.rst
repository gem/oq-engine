Classical PSHA QA test
======================

============== ===================
checksum32     2,024,827,974      
date           2018-04-30T11:21:49
engine_version 3.1.0-gitb0812f0   
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
0_0       CharacteristicFaultSource 11           2.801E-04 1.907E-06  29        3         0     
36_0      CharacteristicFaultSource 11           2.725E-04 1.192E-06  26        2         0     
1_0       CharacteristicFaultSource 11           2.654E-04 9.537E-07  22        2         0     
4_1       CharacteristicFaultSource 11           2.654E-04 9.537E-07  24        2         0     
27_1      CharacteristicFaultSource 11           2.513E-04 1.192E-06  22        2         0     
24_0      CharacteristicFaultSource 11           2.427E-04 9.537E-07  9         2         0     
52_0      CharacteristicFaultSource 11           2.365E-04 9.537E-07  24        2         0     
14_1      CharacteristicFaultSource 11           2.270E-04 1.431E-06  26        2         0     
2_1       CharacteristicFaultSource 11           2.205E-04 9.537E-07  23        2         0     
32_0      CharacteristicFaultSource 11           2.198E-04 9.537E-07  30        2         0     
41_1      CharacteristicFaultSource 11           2.027E-04 1.192E-06  21        2         0     
11_1      CharacteristicFaultSource 11           1.979E-04 9.537E-07  16        1         0     
44_1      CharacteristicFaultSource 11           1.962E-04 1.192E-06  33        2         0     
34_0      CharacteristicFaultSource 11           1.929E-04 1.192E-06  32        2         0     
57_0      CharacteristicFaultSource 11           1.712E-04 9.537E-07  23        2         0     
84_0      CharacteristicFaultSource 11           1.700E-04 1.192E-06  24        2         0     
30_1      CharacteristicFaultSource 11           1.616E-04 9.537E-07  21        2         0     
38_1      CharacteristicFaultSource 11           1.554E-04 1.192E-06  21        2         0     
59_1      CharacteristicFaultSource 11           1.523E-04 1.431E-06  17        2         0     
47_0      CharacteristicFaultSource 11           1.497E-04 1.192E-06  16        2         0     
========= ========================= ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
========================= ========= ======
source_class              calc_time counts
========================= ========= ======
CharacteristicFaultSource 0.01689   246   
========================= ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ======= ========= ======= =========
operation-duration mean    stddev  min       max     num_tasks
count_ruptures     0.00277 0.00167 9.832E-04 0.00771 66       
================== ======= ======= ========= ======= =========

Fastest task
------------
taskno=17, weight=384, duration=0 s, sources="54_1 55_0 55_1 56_0 56_1"

======== ==== ======= === === =
variable mean stddev  min max n
======== ==== ======= === === =
nsites   13   7.34847 7   21  5
weight   76   22      58  100 5
======== ==== ======= === === =

Slowest task
------------
taskno=3, weight=418, duration=0 s, sources="14_1 15_0 15_1 16_0 16_1 18_0 18_1 19_0 19_1"

======== ======= ======= === === =
variable mean    stddev  min max n
======== ======= ======= === === =
nsites   5.00000 3.12250 1   9   9
weight   46      17      22  66  9
======== ======= ======= === === =

Informational data
------------------
============== ================================================================================== ========
task           sent                                                                               received
count_ruptures sources=1.49 MB srcfilter=115.95 KB param=43.18 KB monitor=21.27 KB gsims=14.18 KB 45.05 KB
============== ================================================================================== ========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
reading composite source model 3.06233   0.0       1     
total count_ruptures           0.18271   2.15625   66    
managing sources               0.08229   0.0       1     
store source_info              0.00667   0.0       1     
unpickling count_ruptures      0.00387   0.0       66    
aggregate curves               0.00239   0.0       66    
splitting sources              0.00211   0.0       1     
reading site collection        8.428E-04 0.0       1     
saving probability maps        3.505E-05 0.0       1     
============================== ========= ========= ======