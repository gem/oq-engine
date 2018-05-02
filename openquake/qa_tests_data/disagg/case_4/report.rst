Disaggregation with sampling
============================

============== ===================
checksum32     1,553,247,118      
date           2018-04-30T11:23:03
engine_version 3.1.0-gitb0812f0   
============== ===================

num_sites = 2, num_levels = 38

Parameters
----------
=============================== =================
calculation_mode                'disaggregation' 
number_of_logic_tree_samples    2                
maximum_distance                {'default': 40.0}
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
=============================== =================

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
b1        0.50000 trivial(1)      2/1             
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================= =========== ======================= =================
grp_id gsims             distances   siteparams              ruptparams       
====== ================= =========== ======================= =================
0      ChiouYoungs2008() rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
====== ================= =========== ======================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=2)
  0,ChiouYoungs2008(): [0 1]>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== ============ ============
source_model     grp_id trt                  eff_ruptures tot_ruptures
================ ====== ==================== ============ ============
source_model.xml 0      Active Shallow Crust 1,619        2,236       
================ ====== ==================== ============ ============

Slowest sources
---------------
========= ================== ============ ========= ========== ========= ========= ======
source_id source_class       num_ruptures calc_time split_time num_sites num_split events
========= ================== ============ ========= ========== ========= ========= ======
2         AreaSource         1,440        0.00263   0.01501    96        96        0     
4         ComplexFaultSource 164          0.00119   1.931E-04  10        10        0     
1         PointSource        15           1.659E-04 7.391E-06  1         1         0     
3         SimpleFaultSource  617          0.0       1.321E-04  0         0         0     
========= ================== ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
================== ========= ======
source_class       calc_time counts
================== ========= ======
AreaSource         0.00263   1     
ComplexFaultSource 0.00119   1     
PointSource        1.659E-04 1     
SimpleFaultSource  0.0       1     
================== ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =========
operation-duration mean    stddev  min     max     num_tasks
count_ruptures     0.00475 0.00411 0.00219 0.01482 8        
================== ======= ======= ======= ======= =========

Fastest task
------------
taskno=4, weight=88, duration=0 s, sources="4"

======== ======= ====== === === =
variable mean    stddev min max n
======== ======= ====== === === =
nsites   1.00000 NaN    1   1   1
weight   88      NaN    88  88  1
======== ======= ====== === === =

Slowest task
------------
taskno=1, weight=141, duration=0 s, sources="1 2"

======== ======= ====== ======= ======= ==
variable mean    stddev min     max     n 
======== ======= ====== ======= ======= ==
nsites   1.00000 0.0    1       1       94
weight   1.50000 0.0    1.50000 1.50000 94
======== ======= ====== ======= ======= ==

Informational data
------------------
============== ============================================================================= ========
task           sent                                                                          received
count_ruptures sources=31.96 KB param=6.03 KB srcfilter=6.02 KB monitor=2.58 KB gsims=1016 B 2.93 KB 
============== ============================================================================= ========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
reading composite source model 0.04440   0.0       1     
total count_ruptures           0.03803   1.51562   8     
managing sources               0.02767   0.0       1     
splitting sources              0.01582   0.0       1     
store source_info              0.00319   0.0       1     
unpickling count_ruptures      2.673E-04 0.0       8     
reading site collection        2.565E-04 0.0       1     
aggregate curves               1.242E-04 0.0       8     
saving probability maps        2.599E-05 0.0       1     
============================== ========= ========= ======