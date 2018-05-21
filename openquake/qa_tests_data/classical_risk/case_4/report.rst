Classical Hazard-Risk QA test 4
===============================

============== ===================
checksum32     2,439,591,035      
date           2018-05-15T04:12:34
engine_version 3.1.0-git0acbc11   
============== ===================

num_sites = 6, num_levels = 19

Parameters
----------
=============================== ==================
calculation_mode                'classical'       
number_of_logic_tree_samples    0                 
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
=============================== ==================

Input files
-----------
======================== ============================================================
Name                     File                                                        
======================== ============================================================
exposure                 `exposure_model.xml <exposure_model.xml>`_                  
gsim_logic_tree          `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                  `job_haz.ini <job_haz.ini>`_                                
source                   `source_model.xml <source_model.xml>`_                      
source_model_logic_tree  `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
structural_vulnerability `vulnerability_model.xml <vulnerability_model.xml>`_        
======================== ============================================================

Composite source model
----------------------
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
b1        1.00000 simple(2)       2/2             
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== =================================== =========== ======================= =================
grp_id gsims                               distances   siteparams              ruptparams       
====== =================================== =========== ======================= =================
0      AkkarBommer2010() ChiouYoungs2008() rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
====== =================================== =========== ======================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=2, rlzs=2)
  0,AkkarBommer2010(): [0]
  0,ChiouYoungs2008(): [1]>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== ============ ============
source_model     grp_id trt                  eff_ruptures tot_ruptures
================ ====== ==================== ============ ============
source_model.xml 0      Active Shallow Crust 4,545        91,021      
================ ====== ==================== ============ ============

Exposure model
--------------
=============== ========
#assets         6       
#taxonomies     2       
deductibile     absolute
insurance_limit absolute
=============== ========

======== ======= ====== === === ========= ==========
taxonomy mean    stddev min max num_sites num_assets
W        1.00000 0.0    1   1   5         5         
A        1.00000 NaN    1   1   1         1         
*ALL*    1.00000 0.0    1   1   6         6         
======== ======= ====== === === ========= ==========

Slowest sources
---------------
========= ============ ============ ========= ========== ========= ========= ======
source_id source_class num_ruptures calc_time split_time num_sites num_split events
========= ============ ============ ========= ========== ========= ========= ======
231       AreaSource   4,185        0.00578   0.07523    1,432     279       0     
376       AreaSource   2,220        0.00142   0.04814    36        36        0     
10        AreaSource   1,920        0.0       0.09325    0         0         0     
101       AreaSource   559          0.0       0.01880    0         0         0     
125       AreaSource   8,274        0.0       0.26497    0         0         0     
127       AreaSource   2,940        0.0       0.13520    0         0         0     
13        AreaSource   1,824        0.0       0.07561    0         0         0     
132       AreaSource   4,131        0.0       0.11217    0         0         0     
135       AreaSource   3,285        0.0       0.12212    0         0         0     
137       AreaSource   2,072        0.0       0.07215    0         0         0     
161       AreaSource   552          0.0       0.03099    0         0         0     
166       AreaSource   559          0.0       0.02108    0         0         0     
177       AreaSource   846          0.0       0.03983    0         0         0     
184       AreaSource   780          0.0       0.01550    0         0         0     
198       AreaSource   760          0.0       0.03876    0         0         0     
2         AreaSource   5,446        0.0       0.11362    0         0         0     
20        AreaSource   1,256        0.0       0.04578    0         0         0     
208       AreaSource   760          0.0       0.01787    0         0         0     
225       AreaSource   520          0.0       0.01273    0         0         0     
253       AreaSource   3,058        0.0       0.08117    0         0         0     
========= ============ ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
AreaSource   0.00720   39    
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =========
operation-duration mean    stddev  min     max     num_tasks
prefilter          0.03750 0.01128 0.01481 0.06749 60       
count_ruptures     0.00337 0.00139 0.00162 0.00577 9        
================== ======= ======= ======= ======= =========

Fastest task
------------
taskno=7, weight=239, duration=0 s, sources="231"

======== ======= ======= ======= ======= ==
variable mean    stddev  min     max     n 
======== ======= ======= ======= ======= ==
nsites   5.52941 0.70648 3       6       34
weight   7.03836 0.48275 5.19615 7.34847 34
======== ======= ======= ======= ======= ==

Slowest task
------------
taskno=8, weight=244, duration=0 s, sources="231 376"

======== ======= ======= ======= ======= ==
variable mean    stddev  min     max     n 
======== ======= ======= ======= ======= ==
nsites   3.32075 2.32688 1       6       53
weight   4.60585 2.53690 2.00000 7.34847 53
======== ======= ======= ======= ======= ==

Informational data
------------------
============== ============================================================================ ========
task           sent                                                                         received
prefilter      srcs=1.55 MB monitor=19.1 KB srcfilter=13.42 KB                              81.27 KB
count_ruptures sources=87.49 KB srcfilter=8.7 KB param=4.76 KB monitor=2.93 KB gsims=1.9 KB 3.24 KB 
============== ============================================================================ ========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
splitting sources              2.81529   3.50781   1     
reading composite source model 2.74496   0.0       1     
total prefilter                2.24987   3.37109   60    
managing sources               0.37235   0.0       1     
total count_ruptures           0.03036   0.27734   9     
store source_info              0.00462   0.0       1     
unpickling prefilter           0.00359   0.0       60    
reading site collection        0.00269   0.0       1     
reading exposure               0.00135   0.0       1     
unpickling count_ruptures      3.350E-04 0.0       9     
aggregate curves               1.519E-04 0.0       9     
saving probability maps        3.362E-05 0.0       1     
============================== ========= ========= ======