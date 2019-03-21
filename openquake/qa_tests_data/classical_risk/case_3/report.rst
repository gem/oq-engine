Classical PSHA - Loss fractions QA test
=======================================

============== ===================
checksum32     177,006,542        
date           2019-03-19T10:03:11
engine_version 3.5.0-gitad6b69ea66
============== ===================

num_sites = 12, num_levels = 19, num_rlzs = 1

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
source_model_logic_tree  `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
structural_vulnerability `vulnerability_model.xml <vulnerability_model.xml>`_        
======================== ============================================================

Composite source model
----------------------
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
b1        1.00000 trivial(1)      1               
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== =================== =========== ======================= =================
grp_id gsims               distances   siteparams              ruptparams       
====== =================== =========== ======================= =================
0      '[ChiouYoungs2008]' rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
====== =================== =========== ======================= =================

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)
  0,'[ChiouYoungs2008]': [0]>

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
0      232       A    41    45    1,612        1.95396   3.97404    750       124       395   
0      225       A    38    41    520          0.13558   0.19070    36        18        33    
0      8         A    0     4     4,832        0.0       0.0        0.0       0         0.0   
0      59        A    16    20    750          0.0       0.0        0.0       0         0.0   
0      57        A    12    16    840          0.0       0.0        0.0       0         0.0   
0      42        A    8     12    1,755        0.0       0.0        0.0       0         0.0   
0      359       A    59    63    2,314        0.0       0.0        0.0       0         0.0   
0      306       A    55    59    1,768        0.0       0.0        0.0       0         0.0   
0      299       A    51    55    710          0.0       0.0        0.0       0         0.0   
0      27        A    4     8     1,482        0.0       0.0        0.0       0         0.0   
0      253       A    45    51    3,058        0.0       0.0        0.0       0         0.0   
0      137       A    34    38    2,072        0.0       0.0        0.0       0         0.0   
0      135       A    30    34    3,285        0.0       0.0        0.0       0         0.0   
0      125       A    26    30    8,274        0.0       0.0        0.0       0         0.0   
0      101       A    20    26    559          0.0       0.0        0.0       0         0.0   
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
A    2.08954   15    
==== ========= ======

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
read_source_models 0.98670 NaN     0.98670 0.98670 1      
split_filter       0.31650 NaN     0.31650 0.31650 1      
classical          0.42158 0.14491 0.16285 0.49558 5      
build_hazard_stats 0.00458 0.00149 0.00326 0.00910 12     
================== ======= ======= ======= ======= =======

Fastest task
------------
taskno=4, weight=32, duration=0 s, sources="232"

======== ======= ======= ======= ======= ==
variable mean    stddev  min     max     n 
======== ======= ======= ======= ======= ==
nsites   6.20000 0.63246 5       7       10
weight   3.23313 0.16615 2.90689 3.43948 10
======== ======= ======= ======= ======= ==

Slowest task
------------
taskno=2, weight=99, duration=0 s, sources="232"

======== ======= ======= ======= ======= ==
variable mean    stddev  min     max     n 
======== ======= ======= ======= ======= ==
nsites   6.12903 0.61870 5       7       31
weight   3.21438 0.16337 2.90689 3.43948 31
======== ======= ======= ======= ======= ==

Data transfer
-------------
================== ============================================================= ========
task               sent                                                          received
read_source_models converter=313 B fnames=111 B                                  13.71 KB
split_filter       srcs=16.73 KB srcfilter=1012 B dummy=56 B                     36.53 KB
classical          group=39.42 KB param=2.9 KB src_filter=1.07 KB gsims=775 B    9.73 KB 
build_hazard_stats pgetter=31.72 KB hstats=780 B N=168 B individual_curves=156 B 4.57 KB 
================== ============================================================= ========

Slowest operations
------------------
======================== ========= ========= ======
operation                time_sec  memory_mb counts
======================== ========= ========= ======
total classical          2.10788   1.68359   5     
make_contexts            1.00140   0.0       1,846 
total read_source_models 0.98670   0.23047   1     
get_poes                 0.36599   0.0       1,613 
total split_filter       0.31650   2.75000   1     
total build_hazard_stats 0.05499   1.42969   12    
combine pmaps            0.04873   1.42969   12    
building riskinputs      0.02231   0.0       1     
saving statistics        0.00558   0.0       12    
managing sources         0.00532   0.0       1     
compute stats            0.00326   0.0       9     
store source_info        0.00193   0.0       1     
aggregate curves         0.00164   0.0       5     
saving probability maps  0.00151   0.0       1     
store source model       0.00132   0.0       1     
reading exposure         4.973E-04 0.0       1     
======================== ========= ========= ======