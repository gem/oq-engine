Classical PSHA - Loss fractions QA test
=======================================

============== ===================
checksum32     177,006,542        
date           2018-05-15T04:12:31
engine_version 3.1.0-git0acbc11   
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
232       AreaSource   1,612        0.00188   0.03530    750       124       0     
225       AreaSource   520          5.059E-04 0.01157    36        18        0     
101       AreaSource   559          0.0       0.01870    0         0         0     
125       AreaSource   8,274        0.0       0.25212    0         0         0     
135       AreaSource   3,285        0.0       0.12258    0         0         0     
137       AreaSource   2,072        0.0       0.07183    0         0         0     
253       AreaSource   3,058        0.0       0.07593    0         0         0     
27        AreaSource   1,482        0.0       0.03868    0         0         0     
299       AreaSource   710          0.0       0.01754    0         0         0     
306       AreaSource   1,768        0.0       0.06188    0         0         0     
359       AreaSource   2,314        0.0       0.06034    0         0         0     
42        AreaSource   1,755        0.0       0.03482    0         0         0     
57        AreaSource   840          0.0       0.01603    0         0         0     
59        AreaSource   750          0.0       0.01691    0         0         0     
8         AreaSource   4,832        0.0       0.34058    0         0         0     
========= ============ ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
AreaSource   0.00239   15    
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =========
operation-duration mean    stddev  min     max     num_tasks
prefilter          0.01669 0.00601 0.00640 0.03341 60       
count_ruptures     0.00471 0.00357 0.00219 0.00723 2        
================== ======= ======= ======= ======= =========

Fastest task
------------
taskno=2, weight=84, duration=0 s, sources="232"

======== ======= ======= ======= ======= ==
variable mean    stddev  min     max     n 
======== ======= ======= ======= ======= ==
nsites   6.26923 0.66679 5       7       26
weight   3.25045 0.17530 2.90689 3.43948 26
======== ======= ======= ======= ======= ==

Slowest task
------------
taskno=1, weight=344, duration=0 s, sources="225 232"

======== ======= ======= ======= ======= ===
variable mean    stddev  min     max     n  
======== ======= ======= ======= ======= ===
nsites   5.37069 1.54092 2       7       116
weight   2.97022 0.50643 1.83848 3.43948 116
======== ======= ======= ======= ======= ===

Informational data
------------------
============== ========================================================================== ========
task           sent                                                                       received
prefilter      srcs=603.23 KB monitor=19.1 KB srcfilter=13.42 KB                          40.92 KB
count_ruptures sources=39.19 KB srcfilter=2.57 KB param=1.06 KB monitor=666 B gsims=254 B 791 B   
============== ========================================================================== ========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
reading composite source model 1.18013   0.0       1     
splitting sources              1.17675   1.40625   1     
total prefilter                1.00157   3.03906   60    
managing sources               0.27073   0.0       1     
total count_ruptures           0.00943   0.20703   2     
store source_info              0.00430   0.0       1     
reading site collection        0.00344   0.0       1     
unpickling prefilter           0.00290   0.0       60    
reading exposure               0.00171   0.0       1     
unpickling count_ruptures      7.868E-05 0.0       2     
aggregate curves               4.315E-05 0.0       2     
saving probability maps        3.338E-05 0.0       1     
============================== ========= ========= ======