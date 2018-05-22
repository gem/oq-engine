QA test for disaggregation case_1, taken from the disagg demo
=============================================================

============== ===================
checksum32     1,811,660,702      
date           2018-05-15T04:14:29
engine_version 3.1.0-git0acbc11   
============== ===================

num_sites = 2, num_levels = 38

Parameters
----------
=============================== ==================
calculation_mode                'disaggregation'  
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 100.0}
investigation_time              50.0              
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            5.0               
complex_fault_mesh_spacing      5.0               
width_of_mfd_bin                0.2               
area_source_discretization      10.0              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     9000              
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
source                  `source_model.xml <source_model.xml>`_                      
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
b1        1.00000 trivial(1)      1/1             
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================= =========== ======================= =================
grp_id gsims             distances   siteparams              ruptparams       
====== ================= =========== ======================= =================
0      ChiouYoungs2008() rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
1      ChiouYoungs2008() rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
2      ChiouYoungs2008() rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
3      ChiouYoungs2008() rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
====== ================= =========== ======================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=4, rlzs=1)
  0,ChiouYoungs2008(): [0]
  1,ChiouYoungs2008(): [0]
  2,ChiouYoungs2008(): [0]
  3,ChiouYoungs2008(): [0]>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== ============ ============
source_model     grp_id trt                  eff_ruptures tot_ruptures
================ ====== ==================== ============ ============
source_model.xml 0      Active Shallow Crust 1,631        15          
source_model.xml 1      Active Shallow Crust 1,631        1,440       
source_model.xml 2      Active Shallow Crust 2,116        617         
source_model.xml 3      Active Shallow Crust 303          164         
================ ====== ==================== ============ ============

============= =====
#TRT models   4    
#eff_ruptures 5,681
#tot_ruptures 2,236
#tot_weight   1,418
============= =====

Slowest sources
---------------
========= ================== ============ ========= ========== ========= ========= ======
source_id source_class       num_ruptures calc_time split_time num_sites num_split events
========= ================== ============ ========= ========== ========= ========= ======
2         AreaSource         1,440        0.00686   0.01955    288       288       0     
4         ComplexFaultSource 164          5.517E-04 2.437E-04  12        12        0     
3         SimpleFaultSource  617          4.954E-04 1.771E-04  18        18        0     
1         PointSource        15           1.016E-04 5.484E-06  3         3         0     
========= ================== ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
================== ========= ======
source_class       calc_time counts
================== ========= ======
AreaSource         0.00686   1     
ComplexFaultSource 5.517E-04 1     
PointSource        1.016E-04 1     
SimpleFaultSource  4.954E-04 1     
================== ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =========
operation-duration mean    stddev  min     max     num_tasks
prefilter          0.00479 0.00260 0.00194 0.01521 59       
count_ruptures     0.00482 0.00611 0.00140 0.01572 5        
================== ======= ======= ======= ======= =========

Fastest task
------------
taskno=2, weight=302, duration=0 s, sources="3"

======== ======= ====== === === =
variable mean    stddev min max n
======== ======= ====== === === =
nsites   1.00000 0.0    1   1   4
weight   75      14     63  88  4
======== ======= ====== === === =

Slowest task
------------
taskno=1, weight=321, duration=0 s, sources="1 2 3"

======== ======= ====== ======= === ==
variable mean    stddev min     max n 
======== ======= ====== ======= === ==
nsites   1.00000 0.0    1       1   99
weight   3.24747 12     1.50000 88  99
======== ======= ====== ======= === ==

Informational data
------------------
============== ============================================================================ ========
task           sent                                                                         received
prefilter      srcs=81.54 KB monitor=18.78 KB srcfilter=13.19 KB                            88.79 KB
count_ruptures sources=45.46 KB param=3.77 KB srcfilter=3.76 KB monitor=1.63 KB gsims=635 B 1.97 KB 
============== ============================================================================ ========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total prefilter                0.28236   3.43359   59    
managing sources               0.22172   0.0       1     
reading composite source model 0.05567   0.0       1     
total count_ruptures           0.02412   0.0       5     
splitting sources              0.02065   0.0       1     
unpickling prefilter           0.00633   0.0       59    
store source_info              0.00405   0.0       1     
reading site collection        3.023E-04 0.0       1     
unpickling count_ruptures      2.415E-04 0.0       5     
aggregate curves               1.292E-04 0.0       5     
saving probability maps        3.552E-05 0.0       1     
============================== ========= ========= ======