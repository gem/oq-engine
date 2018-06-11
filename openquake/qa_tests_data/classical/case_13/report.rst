Classical PSHA QA test
======================

============== ===================
checksum32     2,024,827,974      
date           2018-06-05T06:38:47
engine_version 3.2.0-git65c4735   
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
4_1       CharacteristicFaultSource 11           0.01324   9.537E-07  12        2         0     
14_1      CharacteristicFaultSource 11           0.01147   1.192E-06  13        2         0     
24_0      CharacteristicFaultSource 11           0.01111   9.537E-07  4.50000   2         0     
41_1      CharacteristicFaultSource 11           0.01103   9.537E-07  10        2         0     
2_1       CharacteristicFaultSource 11           0.01100   1.192E-06  11        2         0     
0_0       CharacteristicFaultSource 11           0.01062   2.146E-06  9.66667   3         0     
11_1      CharacteristicFaultSource 11           0.01061   9.537E-07  16        1         0     
34_0      CharacteristicFaultSource 11           0.01040   1.192E-06  16        2         0     
1_0       CharacteristicFaultSource 11           0.01037   9.537E-07  11        2         0     
27_1      CharacteristicFaultSource 11           0.01020   9.537E-07  11        2         0     
57_0      CharacteristicFaultSource 11           0.00963   1.192E-06  11        2         0     
38_1      CharacteristicFaultSource 11           0.00864   9.537E-07  10        2         0     
47_0      CharacteristicFaultSource 11           0.00807   1.192E-06  8.00000   2         0     
59_1      CharacteristicFaultSource 11           0.00802   1.192E-06  8.50000   2         0     
36_0      CharacteristicFaultSource 11           0.00781   9.537E-07  13        2         0     
32_0      CharacteristicFaultSource 11           0.00775   9.537E-07  15        2         0     
54_1      CharacteristicFaultSource 11           0.00747   9.537E-07  6.00000   2         0     
61_1      CharacteristicFaultSource 11           0.00716   1.192E-06  21        1         0     
66_0      CharacteristicFaultSource 11           0.00704   9.537E-07  13        2         0     
74_0      CharacteristicFaultSource 11           0.00701   1.431E-06  16        2         0     
========= ========================= ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
========================= ========= ======
source_class              calc_time counts
========================= ========= ======
CharacteristicFaultSource 0.34275   246   
========================= ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =========
operation-duration mean    stddev  min     max     num_tasks
RtreeFilter        0.00886 0.00472 0.00188 0.02365 54       
count_eff_ruptures 0.00778 0.00377 0.00289 0.01735 66       
================== ======= ======= ======= ======= =========

Fastest task
------------
taskno=61, weight=436, duration=0 s, sources="84_1 85_0 85_1 86_0 86_1"

======== ==== ======= === === =
variable mean stddev  min max n
======== ==== ======= === === =
nsites   15   1.64317 13  17  5
weight   87   4.68637 79  90  5
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

Data transfer
-------------
================== ================================================================================= ========
task               sent                                                                              received
RtreeFilter        srcs=1.53 MB monitor=18.25 KB srcfilter=14.71 KB                                  1.46 MB 
count_eff_ruptures sources=1.48 MB param=44.41 KB monitor=22.75 KB srcfilter=15.02 KB gsims=14.18 KB 45.05 KB
================== ================================================================================= ========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
PSHACalculator.run             4.00788   4.87500   1     
reading composite source model 3.10787   3.19531   1     
total count_eff_ruptures       0.51357   5.90625   66    
total prefilter                0.47837   3.66016   54    
managing sources               0.40609   1.57812   1     
unpickling prefilter           0.04877   0.25781   54    
aggregate curves               0.02678   0.0       66    
unpickling count_eff_ruptures  0.02186   0.0       66    
store source_info              0.00819   0.0       1     
splitting sources              0.00194   0.0       1     
reading site collection        0.00139   0.0       1     
saving probability maps        1.943E-04 0.0       1     
============================== ========= ========= ======