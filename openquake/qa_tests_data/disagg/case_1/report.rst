QA test for disaggregation case_1, taken from the disagg demo
=============================================================

============== ===================
checksum32     1,811,660,702      
date           2018-06-05T06:40:13
engine_version 3.2.0-git65c4735   
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
3         SimpleFaultSource  617          0.01362   1.514E-04  1.00000   18        0     
4         ComplexFaultSource 164          0.01183   1.967E-04  1.00000   12        0     
1         PointSource        15           0.00657   8.106E-06  1.00000   3         0     
2         AreaSource         1,440        0.00533   0.02915    1.00000   288       0     
========= ================== ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
================== ========= ======
source_class       calc_time counts
================== ========= ======
AreaSource         0.00533   1     
ComplexFaultSource 0.01183   1     
PointSource        0.00657   1     
SimpleFaultSource  0.01362   1     
================== ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =========
operation-duration mean    stddev  min     max     num_tasks
RtreeFilter        0.00409 0.00254 0.00100 0.00985 59       
count_eff_ruptures 0.01158 0.00670 0.00731 0.02343 5        
================== ======= ======= ======= ======= =========

Fastest task
------------
taskno=5, weight=152, duration=0 s, sources="4"

======== ======= ====== ======= === =
variable mean    stddev min     max n
======== ======= ====== ======= === =
nsites   1.00000 0.0    1       1   4
weight   38      26     4.00000 64  4
======== ======= ====== ======= === =

Slowest task
------------
taskno=1, weight=321, duration=0 s, sources="1 2 3"

======== ======= ====== ======= === ==
variable mean    stddev min     max n 
======== ======= ====== ======= === ==
nsites   1.00000 0.0    1       1   99
weight   3.24747 12     1.50000 88  99
======== ======= ====== ======= === ==

Data transfer
-------------
================== ============================================================================ ========
task               sent                                                                         received
RtreeFilter        srcs=81.54 KB monitor=19.94 KB srcfilter=16.08 KB                            88.79 KB
count_eff_ruptures sources=45.46 KB param=3.86 KB monitor=1.72 KB srcfilter=1.14 KB gsims=635 B 1.97 KB 
================== ============================================================================ ========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
PSHACalculator.run             0.70670   0.0       1     
managing sources               0.43337   0.0       1     
total prefilter                0.24110   3.46875   59    
reading composite source model 0.06966   0.0       1     
total count_eff_ruptures       0.05790   5.77344   5     
splitting sources              0.03022   0.0       1     
unpickling prefilter           0.02087   0.0       59    
store source_info              0.00619   0.0       1     
aggregate curves               0.00163   0.0       5     
unpickling count_eff_ruptures  0.00129   0.0       5     
reading site collection        6.719E-04 0.0       1     
saving probability maps        1.986E-04 0.0       1     
============================== ========= ========= ======