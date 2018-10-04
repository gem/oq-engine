Classical PSHA - Loss fractions QA test
=======================================

============== ===================
checksum32     177,006,542        
date           2018-10-03T15:00:25
engine_version 3.3.0-gitd9f5dca908
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
source_model.xml 0      Active Shallow Crust 1,613        33,831      
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
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======
grp_id source_id code gidx1 gidx2 num_ruptures calc_time split_time num_sites num_split weight
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======
0      8         A    0     4     4,832        0.0       0.0        0.0       0         0.0   
0      27        A    4     8     1,482        0.0       0.0        0.0       0         0.0   
0      42        A    8     12    1,755        0.0       0.0        0.0       0         0.0   
0      57        A    12    16    840          0.0       0.0        0.0       0         0.0   
0      59        A    16    20    750          0.0       0.0        0.0       0         0.0   
0      101       A    20    26    559          0.0       0.0        0.0       0         0.0   
0      125       A    26    30    8,274        0.0       0.0        0.0       0         0.0   
0      135       A    30    34    3,285        0.0       0.0        0.0       0         0.0   
0      137       A    34    38    2,072        0.0       0.0        0.0       0         0.0   
0      225       A    38    41    520          0.31322   0.34340    36        18        33    
0      232       A    41    45    1,612        3.60089   6.98183    750       124       395   
0      253       A    45    51    3,058        0.0       0.0        0.0       0         0.0   
0      299       A    51    55    710          0.0       0.0        0.0       0         0.0   
0      306       A    55    59    1,768        0.0       0.0        0.0       0         0.0   
0      359       A    59    63    2,314        0.0       0.0        0.0       0         0.0   
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
A    3.91412   15    
==== ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
read_source_models 1.91911 NaN     1.91911 1.91911 1      
split_filter       0.48465 NaN     0.48465 0.48465 1      
classical          1.96445 1.50444 0.90065 3.02824 2      
build_hazard_stats 0.00881 0.00608 0.00563 0.02214 12     
================== ======= ======= ======= ======= =======

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
taskno=1, weight=345, duration=3 s, sources="225 232"

======== ======= ======= ======= ======= ===
variable mean    stddev  min     max     n  
======== ======= ======= ======= ======= ===
nsites   5.41379 1.56076 2       7       116
weight   2.98160 0.51148 1.83848 3.43948 116
======== ======= ======= ======= ======= ===

Data transfer
-------------
================== =========================================================================== ========
task               sent                                                                        received
read_source_models monitor=0 B fnames=0 B converter=0 B                                        13.32 KB
split_filter       srcs=16.36 KB monitor=1.73 KB srcfilter=1012 B sample_factor=84 B seed=56 B 36.13 KB
classical          group=36.93 KB param=1.24 KB monitor=690 B src_filter=440 B gsims=254 B     4.15 KB 
build_hazard_stats pgetter=29.71 KB monitor=4.15 KB hstats=804 B                               4.57 KB 
================== =========================================================================== ========

Slowest operations
------------------
======================== ========= ========= ======
operation                time_sec  memory_mb counts
======================== ========= ========= ======
total classical          3.92889   0.60156   2     
total read_source_models 1.91911   0.39062   1     
make_contexts            1.83923   0.0       1,846 
iter_ruptures            1.33506   0.0       142   
updating source_info     1.05519   0.39062   1     
get_poes                 0.69777   0.0       1,613 
total split_filter       0.48465   1.34375   1     
total build_hazard_stats 0.10567   0.72266   12    
combine pmaps            0.09797   0.72266   12    
building riskinputs      0.04267   0.0       1     
managing sources         0.02031   0.0       1     
saving statistics        0.00790   0.0       12    
store source_info        0.00614   0.0       2     
compute mean             0.00423   0.0       9     
saving probability maps  0.00213   0.0       1     
reading exposure         7.470E-04 0.0       1     
aggregate curves         5.946E-04 0.0       2     
======================== ========= ========= ======