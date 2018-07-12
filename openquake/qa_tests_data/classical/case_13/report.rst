Classical PSHA QA test
======================

============== ===================
checksum32     2,024,827,974      
date           2018-06-26T14:57:24
engine_version 3.2.0-gitb0cd949   
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
24_0      CharacteristicFaultSource 11           0.01438   9.537E-07  4.50000   2         0     
44_1      CharacteristicFaultSource 11           0.01148   1.192E-06  16        2         0     
14_1      CharacteristicFaultSource 11           0.01070   1.431E-06  13        2         0     
0_0       CharacteristicFaultSource 11           0.01044   2.384E-06  9.66667   3         0     
1_0       CharacteristicFaultSource 11           0.01042   9.537E-07  11        2         0     
32_0      CharacteristicFaultSource 11           0.01031   1.192E-06  15        2         0     
27_1      CharacteristicFaultSource 11           0.01024   1.264E-05  11        2         0     
54_1      CharacteristicFaultSource 11           0.01007   1.192E-06  6.00000   2         0     
4_1       CharacteristicFaultSource 11           0.00906   1.192E-06  12        2         0     
41_1      CharacteristicFaultSource 11           0.00806   1.192E-06  10        2         0     
47_0      CharacteristicFaultSource 11           0.00805   1.669E-06  8.00000   2         0     
89_0      CharacteristicFaultSource 11           0.00793   1.192E-06  17        2         0     
34_0      CharacteristicFaultSource 11           0.00758   1.192E-06  16        2         0     
11_1      CharacteristicFaultSource 11           0.00754   9.537E-07  16        1         0     
2_1       CharacteristicFaultSource 11           0.00751   1.192E-06  11        2         0     
61_1      CharacteristicFaultSource 11           0.00739   1.192E-06  21        1         0     
38_1      CharacteristicFaultSource 11           0.00716   1.431E-06  10        2         0     
57_0      CharacteristicFaultSource 11           0.00716   1.192E-06  11        2         0     
52_0      CharacteristicFaultSource 11           0.00609   1.192E-06  12        2         0     
59_1      CharacteristicFaultSource 11           0.00598   1.192E-06  8.50000   2         0     
========= ========================= ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
========================= ========= ======
source_class              calc_time counts
========================= ========= ======
CharacteristicFaultSource 0.32261   246   
========================= ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =========
operation-duration mean    stddev  min     max     num_tasks
RtreeFilter        0.00707 0.00318 0.00272 0.01565 54       
count_eff_ruptures 0.00750 0.00367 0.00304 0.01618 66       
================== ======= ======= ======= ======= =========

Fastest task
------------
taskno=31, weight=420, duration=0 s, sources="86_1 87_0 87_1 88_0 88_1"

======== ==== ======= === === =
variable mean stddev  min max n
======== ==== ======= === === =
nsites   14   0.54772 14  15  5
weight   84   1.58247 82  85  5
======== ==== ======= === === =

Slowest task
------------
taskno=13, weight=436, duration=0 s, sources="44_1 45_0 45_1 46_0 46_1"

======== ==== ======= === === =
variable mean stddev  min max n
======== ==== ======= === === =
nsites   15   2.04939 14  19  5
weight   87   5.57984 82  95  5
======== ==== ======= === === =

Data transfer
-------------
================== ================================================================================= ========
task               sent                                                                              received
RtreeFilter        srcs=1.53 MB monitor=16.98 KB srcfilter=14.71 KB                                  1.46 MB 
count_eff_ruptures sources=1.48 MB param=44.41 KB monitor=21.21 KB srcfilter=15.86 KB gsims=14.18 KB 45.05 KB
================== ================================================================================= ========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
reading composite source model 3.22338   2.65625   1     
total count_eff_ruptures       0.49514   6.53906   66    
managing sources               0.39349   1.64453   1     
total prefilter                0.38172   3.32031   54    
unpickling prefilter           0.04332   0.25391   54    
unpickling count_eff_ruptures  0.02127   0.0       66    
aggregate curves               0.02079   0.0       66    
store source_info              0.00814   0.0       1     
splitting sources              0.00210   0.0       1     
reading site collection        5.865E-04 0.0       1     
============================== ========= ========= ======