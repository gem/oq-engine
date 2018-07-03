Disaggregation with sampling
============================

============== ===================
checksum32     1,553,247,118      
date           2018-06-05T06:40:11
engine_version 3.2.0-git65c4735   
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
4         ComplexFaultSource 164          0.04129   1.960E-04  1.00000   10        0     
2         AreaSource         1,440        0.00983   0.01699    1.00000   96        0     
1         PointSource        15           0.00564   5.960E-06  1.00000   1         0     
3         SimpleFaultSource  617          0.0       1.626E-04  0.0       0         0     
========= ================== ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
================== ========= ======
source_class       calc_time counts
================== ========= ======
AreaSource         0.00983   1     
ComplexFaultSource 0.04129   1     
PointSource        0.00564   1     
SimpleFaultSource  0.0       1     
================== ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =========
operation-duration mean    stddev  min     max     num_tasks
RtreeFilter        0.00373 0.00205 0.00104 0.00893 59       
count_eff_ruptures 0.00992 0.00215 0.00784 0.01482 8        
================== ======= ======= ======= ======= =========

Fastest task
------------
taskno=7, weight=140, duration=0 s, sources="4"

======== ======= ======= === === =
variable mean    stddev  min max n
======== ======= ======= === === =
nsites   1.00000 0.0     1   1   2
weight   70      8.48528 64  76  2
======== ======= ======= === === =

Slowest task
------------
taskno=1, weight=141, duration=0 s, sources="1 2"

======== ======= ====== ======= ======= ==
variable mean    stddev min     max     n 
======== ======= ====== ======= ======= ==
nsites   1.00000 0.0    1       1       94
weight   1.50000 0.0    1.50000 1.50000 94
======== ======= ====== ======= ======= ==

Data transfer
-------------
================== ============================================================================= ========
task               sent                                                                          received
RtreeFilter        srcs=81.48 KB monitor=19.94 KB srcfilter=16.08 KB                             82.6 KB 
count_eff_ruptures sources=44.09 KB param=6.18 KB monitor=2.76 KB srcfilter=1.82 KB gsims=1016 B 2.93 KB 
================== ============================================================================= ========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
PSHACalculator.run             0.68086   0.0       1     
managing sources               0.41733   0.0       1     
total prefilter                0.21990   3.46875   59    
total count_eff_ruptures       0.07936   5.87891   8     
reading composite source model 0.05259   0.0       1     
unpickling prefilter           0.02056   0.0       59    
splitting sources              0.01775   0.0       1     
store source_info              0.00585   0.0       1     
aggregate curves               0.00229   0.0       8     
unpickling count_eff_ruptures  0.00194   0.0       8     
reading site collection        7.403E-04 0.0       1     
saving probability maps        1.955E-04 0.0       1     
============================== ========= ========= ======