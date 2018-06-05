Classical Hazard-Risk QA test 4
===============================

============== ===================
checksum32     3,002,809,595      
date           2018-06-05T06:38:14
engine_version 3.2.0-git65c4735   
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
231       AreaSource   4,185        0.05683   0.06908    5.13262   279       0     
376       AreaSource   2,220        0.00820   0.04681    1.00000   36        0     
10        AreaSource   1,920        0.0       0.09298    0.0       0         0     
101       AreaSource   559          0.0       0.01851    0.0       0         0     
125       AreaSource   8,274        0.0       0.25247    0.0       0         0     
127       AreaSource   2,940        0.0       0.13765    0.0       0         0     
13        AreaSource   1,824        0.0       0.07656    0.0       0         0     
132       AreaSource   4,131        0.0       0.11150    0.0       0         0     
135       AreaSource   3,285        0.0       0.12064    0.0       0         0     
137       AreaSource   2,072        0.0       0.07120    0.0       0         0     
161       AreaSource   552          0.0       0.03099    0.0       0         0     
166       AreaSource   559          0.0       0.02101    0.0       0         0     
177       AreaSource   846          0.0       0.04007    0.0       0         0     
184       AreaSource   780          0.0       0.01580    0.0       0         0     
198       AreaSource   760          0.0       0.03902    0.0       0         0     
2         AreaSource   5,446        0.0       0.11253    0.0       0         0     
20        AreaSource   1,256        0.0       0.04272    0.0       0         0     
208       AreaSource   760          0.0       0.01647    0.0       0         0     
225       AreaSource   520          0.0       0.01184    0.0       0         0     
253       AreaSource   3,058        0.0       0.07918    0.0       0         0     
========= ============ ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
AreaSource   0.06503   39    
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =========
operation-duration mean    stddev  min     max     num_tasks
RtreeFilter        0.03744 0.01506 0.01318 0.08261 60       
count_eff_ruptures 0.01139 0.00173 0.00940 0.01450 9        
================== ======= ======= ======= ======= =========

Fastest task
------------
taskno=5, weight=243, duration=0 s, sources="231"

======== ======= ======= ======= ======= ==
variable mean    stddev  min     max     n 
======== ======= ======= ======= ======= ==
nsites   4.65789 1.21425 2       6       38
weight   6.41463 0.89132 4.24264 7.34847 38
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

Data transfer
-------------
================== ============================================================================ ========
task               sent                                                                         received
RtreeFilter        srcs=1.55 MB monitor=20.27 KB srcfilter=16.35 KB                             81.27 KB
count_eff_ruptures sources=87.49 KB param=4.98 KB monitor=3.1 KB srcfilter=2.05 KB gsims=1.9 KB 3.24 KB 
================== ============================================================================ ========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
PSHACalculator.run             6.15775   6.13281   1     
splitting sources              2.76890   4.00000   1     
reading composite source model 2.72968   0.08594   1     
total prefilter                2.24631   3.41797   60    
managing sources               0.47475   0.76953   1     
total count_eff_ruptures       0.10252   5.89844   9     
unpickling prefilter           0.01558   0.0       60    
store source_info              0.00585   0.76562   1     
aggregate curves               0.00272   0.0       9     
unpickling count_eff_ruptures  0.00252   0.0       9     
reading site collection        0.00220   0.0       1     
reading exposure               0.00125   0.0       1     
saving probability maps        1.969E-04 0.0       1     
============================== ========= ========= ======