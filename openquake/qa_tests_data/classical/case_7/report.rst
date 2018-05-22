Classical Hazard QA Test, Case 7
================================

============== ===================
checksum32     359,954,679        
date           2018-05-15T04:13:31
engine_version 3.1.0-git0acbc11   
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
0      SadighEtAl1997() rjb rrup  vs30       mag rake  
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
1         SimpleFaultSource  91           7.820E-05 4.530E-06  1         1         0     
2         ComplexFaultSource 49           4.864E-05 3.338E-06  1         1         0     
========= ================== ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
================== ========= ======
source_class       calc_time counts
================== ========= ======
ComplexFaultSource 4.864E-05 1     
SimpleFaultSource  7.820E-05 1     
================== ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ========= ======= ======= =========
operation-duration mean    stddev    min     max     num_tasks
prefilter          0.00756 1.942E-04 0.00739 0.00777 3        
count_ruptures     0.00242 6.371E-04 0.00197 0.00287 2        
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

Informational data
------------------
============== ====================================================================== ========
task           sent                                                                   received
prefilter      srcs=3.23 KB monitor=978 B srcfilter=687 B                             3.56 KB 
count_ruptures sources=2.49 KB srcfilter=1.4 KB param=824 B monitor=666 B gsims=240 B 716 B   
============== ====================================================================== ========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
reading composite source model 0.20189   0.0       1     
managing sources               0.02801   0.0       1     
total prefilter                0.02269   4.01172   3     
store source_info              0.00694   0.0       1     
total count_ruptures           0.00483   0.83203   2     
splitting sources              5.338E-04 0.0       1     
reading site collection        2.918E-04 0.0       1     
unpickling prefilter           2.689E-04 0.0       3     
unpickling count_ruptures      1.249E-04 0.0       2     
aggregate curves               7.176E-05 0.0       2     
saving probability maps        5.150E-05 0.0       1     
============================== ========= ========= ======