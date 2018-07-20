Classical Hazard QA Test, Case 7
================================

============== ===================
checksum32     359,954,679        
date           2018-06-26T14:57:49
engine_version 3.2.0-gitb0cd949   
============== ===================

num_sites = 1, num_levels = 3

Parameters
----------
=============================== ==================
calculation_mode                'classical'       
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              1.0               
ses_per_logic_tree_path         1                 
truncation_level                0.0               
rupture_mesh_spacing            0.1               
complex_fault_mesh_spacing      0.1               
width_of_mfd_bin                1.0               
area_source_discretization      10.0              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     1066              
master_seed                     0                 
ses_seed                        42                
=============================== ==================

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
b1        0.70000 trivial(1)      1/1             
b2        0.30000 trivial(1)      0/1             
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================ ========= ========== ==========
grp_id gsims            distances siteparams ruptparams
====== ================ ========= ========== ==========
0      SadighEtAl1997() rrup      vs30       mag rake  
====== ================ ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)
  0,SadighEtAl1997(): [0]>

Number of ruptures per tectonic region type
-------------------------------------------
================== ====== ==================== ============ ============
source_model       grp_id trt                  eff_ruptures tot_ruptures
================== ====== ==================== ============ ============
source_model_1.xml 0      Active Shallow Crust 140          140         
================== ====== ==================== ============ ============

Slowest sources
---------------
========= ================== ============ ========= ========== ========= ========= ======
source_id source_class       num_ruptures calc_time split_time num_sites num_split events
========= ================== ============ ========= ========== ========= ========= ======
1         SimpleFaultSource  91           0.00431   5.007E-06  1.00000   1         0     
2         ComplexFaultSource 49           0.00425   3.099E-06  1.00000   1         0     
========= ================== ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
================== ========= ======
source_class       calc_time counts
================== ========= ======
ComplexFaultSource 0.00425   1     
SimpleFaultSource  0.00431   1     
================== ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ========= ======= ======= =========
operation-duration mean    stddev    min     max     num_tasks
RtreeFilter        0.00538 0.00168   0.00416 0.00729 3        
count_eff_ruptures 0.00565 8.227E-05 0.00559 0.00571 2        
================== ======= ========= ======= ======= =========

Fastest task
------------
taskno=2, weight=196, duration=0 s, sources="2"

======== ======= ====== === === =
variable mean    stddev min max n
======== ======= ====== === === =
nsites   1.00000 NaN    1   1   1
weight   196     NaN    196 196 1
======== ======= ====== === === =

Slowest task
------------
taskno=1, weight=91, duration=0 s, sources="1"

======== ======= ====== === === =
variable mean    stddev min max n
======== ======= ====== === === =
nsites   1.00000 NaN    1   1   1
weight   91      NaN    91  91  1
======== ======= ====== === === =

Data transfer
-------------
================== ===================================================================== ========
task               sent                                                                  received
RtreeFilter        srcs=3.23 KB monitor=966 B srcfilter=837 B                            3.56 KB 
count_eff_ruptures sources=2.49 KB param=862 B monitor=658 B srcfilter=492 B gsims=240 B 716 B   
================== ===================================================================== ========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
reading composite source model 0.19229   0.0       1     
managing sources               0.10483   0.0       1     
total prefilter                0.01613   4.17969   3     
total count_eff_ruptures       0.01131   6.42969   2     
store source_info              0.00607   0.0       1     
unpickling prefilter           7.885E-04 0.0       3     
unpickling count_eff_ruptures  4.709E-04 0.0       2     
aggregate curves               4.585E-04 0.0       2     
reading site collection        3.459E-04 0.0       1     
splitting sources              3.216E-04 0.0       1     
============================== ========= ========= ======