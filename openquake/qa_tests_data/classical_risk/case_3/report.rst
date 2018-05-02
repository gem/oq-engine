Classical PSHA - Loss fractions QA test
=======================================

============== ===================
checksum32     177,006,542        
date           2018-04-30T11:21:18
engine_version 3.1.0-gitb0812f0   
============== ===================

num_sites = 12, num_levels = 19

Parameters
----------
=============================== ==================
calculation_mode                'classical_risk'  
number_of_logic_tree_samples    1                 
maximum_distance                {'default': 200.0}
investigation_time              50.0              
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            5.0               
complex_fault_mesh_spacing      5.0               
width_of_mfd_bin                0.2               
area_source_discretization      10.0              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     23                
master_seed                     0                 
ses_seed                        42                
avg_losses                      True              
=============================== ==================

Input files
-----------
======================== ============================================================
Name                     File                                                        
======================== ============================================================
exposure                 `exposure_model.xml <exposure_model.xml>`_                  
gsim_logic_tree          `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                  `job.ini <job.ini>`_                                        
source                   `source_model.xml <source_model.xml>`_                      
source_model_logic_tree  `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
structural_vulnerability `vulnerability_model.xml <vulnerability_model.xml>`_        
======================== ============================================================

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
====== ================= =========== ======================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)
  0,ChiouYoungs2008(): [0]>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== ============ ============
source_model     grp_id trt                  eff_ruptures tot_ruptures
================ ====== ==================== ============ ============
source_model.xml 0      Active Shallow Crust 1,846        33,831      
================ ====== ==================== ============ ============

Exposure model
--------------
=============== ========
#assets         13      
#taxonomies     4       
deductibile     absolute
insurance_limit absolute
=============== ========

======== ======= ======= === === ========= ==========
taxonomy mean    stddev  min max num_sites num_assets
W        1.00000 0.0     1   1   5         5         
A        1.00000 0.0     1   1   4         4         
DS       2.00000 NaN     2   2   1         2         
UFB      1.00000 0.0     1   1   2         2         
*ALL*    1.08333 0.28868 1   2   12        13        
======== ======= ======= === === ========= ==========

Slowest sources
---------------
========= ============ ============ ========= ========== ========= ========= ======
source_id source_class num_ruptures calc_time split_time num_sites num_split events
========= ============ ============ ========= ========== ========= ========= ======
232       AreaSource   1,612        0.00217   0.03315    750       124       0     
225       AreaSource   520          4.430E-04 0.01117    36        18        0     
101       AreaSource   559          0.0       0.01759    0         0         0     
125       AreaSource   8,274        0.0       0.24921    0         0         0     
135       AreaSource   3,285        0.0       0.12003    0         0         0     
137       AreaSource   2,072        0.0       0.06928    0         0         0     
253       AreaSource   3,058        0.0       0.07548    0         0         0     
27        AreaSource   1,482        0.0       0.03750    0         0         0     
299       AreaSource   710          0.0       0.01666    0         0         0     
306       AreaSource   1,768        0.0       0.05912    0         0         0     
359       AreaSource   2,314        0.0       0.05736    0         0         0     
42        AreaSource   1,755        0.0       0.03327    0         0         0     
57        AreaSource   840          0.0       0.01523    0         0         0     
59        AreaSource   750          0.0       0.01630    0         0         0     
8         AreaSource   4,832        0.0       0.32245    0         0         0     
========= ============ ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
AreaSource   0.00261   15    
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =========
operation-duration mean    stddev  min     max     num_tasks
count_ruptures     0.00684 0.00489 0.00339 0.01030 2        
================== ======= ======= ======= ======= =========

Fastest task
------------
taskno=2, weight=83, duration=0 s, sources="232"

======== ======= ======= ======= ======= ==
variable mean    stddev  min     max     n 
======== ======= ======= ======= ======= ==
nsites   6.07692 0.68836 5       7       26
weight   3.19967 0.18270 2.90689 3.43948 26
======== ======= ======= ======= ======= ==

Slowest task
------------
taskno=1, weight=345, duration=0 s, sources="225 232"

======== ======= ======= ======= ======= ===
variable mean    stddev  min     max     n  
======== ======= ======= ======= ======= ===
nsites   5.41379 1.56076 2       7       116
weight   2.98160 0.51148 1.83848 3.43948 116
======== ======= ======= ======= ======= ===

Informational data
------------------
============== ========================================================================== ========
task           sent                                                                       received
count_ruptures sources=40.43 KB srcfilter=2.56 KB param=1.06 KB monitor=660 B gsims=254 B 791 B   
============== ========================================================================== ========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
splitting sources              1.13581   1.54297   1     
reading composite source model 1.10439   0.0       1     
managing sources               0.22197   0.0       1     
total count_ruptures           0.01368   1.93359   2     
reading exposure               0.00363   0.0       1     
reading site collection        0.00345   0.0       1     
store source_info              0.00316   0.0       1     
unpickling count_ruptures      7.319E-05 0.0       2     
aggregate curves               3.719E-05 0.0       2     
saving probability maps        2.623E-05 0.0       1     
============================== ========= ========= ======