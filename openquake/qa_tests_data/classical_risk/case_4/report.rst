Classical Hazard-Risk QA test 4
===============================

============== ===================
checksum32     2,439,591,035      
date           2018-04-30T11:21:21
engine_version 3.1.0-gitb0812f0   
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
231       AreaSource   4,185        0.00819   0.07225    1,432     279       0     
376       AreaSource   2,220        0.00221   0.04729    36        36        0     
10        AreaSource   1,920        0.0       0.09400    0         0         0     
101       AreaSource   559          0.0       0.01854    0         0         0     
125       AreaSource   8,274        0.0       0.25042    0         0         0     
127       AreaSource   2,940        0.0       0.12957    0         0         0     
13        AreaSource   1,824        0.0       0.07336    0         0         0     
132       AreaSource   4,131        0.0       0.11088    0         0         0     
135       AreaSource   3,285        0.0       0.11917    0         0         0     
137       AreaSource   2,072        0.0       0.07120    0         0         0     
161       AreaSource   552          0.0       0.03160    0         0         0     
166       AreaSource   559          0.0       0.02179    0         0         0     
177       AreaSource   846          0.0       0.04117    0         0         0     
184       AreaSource   780          0.0       0.01592    0         0         0     
198       AreaSource   760          0.0       0.04003    0         0         0     
2         AreaSource   5,446        0.0       0.15095    0         0         0     
20        AreaSource   1,256        0.0       0.04479    0         0         0     
208       AreaSource   760          0.0       0.01740    0         0         0     
225       AreaSource   520          0.0       0.01243    0         0         0     
253       AreaSource   3,058        0.0       0.07873    0         0         0     
========= ============ ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
AreaSource   0.01040   39    
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =========
operation-duration mean    stddev  min     max     num_tasks
count_ruptures     0.00751 0.00134 0.00571 0.00875 9        
================== ======= ======= ======= ======= =========

Fastest task
------------
taskno=2, weight=241, duration=0 s, sources="231"

======== ======= ======= ======= ======= ==
variable mean    stddev  min     max     n 
======== ======= ======= ======= ======= ==
nsites   5.61765 0.55129 4       6       34
weight   7.10166 0.35915 6.00000 7.34847 34
======== ======= ======= ======= ======= ==

Slowest task
------------
taskno=7, weight=238, duration=0 s, sources="231"

======== ======= ======= ======= ======= ==
variable mean    stddev  min     max     n 
======== ======= ======= ======= ======= ==
nsites   4.70270 1.30947 2       6       37
weight   6.43468 0.97200 4.24264 7.34847 37
======== ======= ======= ======= ======= ==

Informational data
------------------
============== ============================================================================ ========
task           sent                                                                         received
count_ruptures sources=90.11 KB srcfilter=8.69 KB param=4.76 KB monitor=2.9 KB gsims=1.9 KB 3.24 KB 
============== ============================================================================ ========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
splitting sources              2.74431   6.19531   1     
reading composite source model 2.74408   0.0       1     
managing sources               0.60504   0.0       1     
total count_ruptures           0.06763   2.03125   9     
store source_info              0.00371   0.0       1     
reading exposure               0.00335   0.0       1     
reading site collection        0.00266   0.0       1     
unpickling count_ruptures      3.211E-04 0.0       9     
aggregate curves               1.414E-04 0.0       9     
saving probability maps        2.766E-05 0.0       1     
============================== ========= ========= ======