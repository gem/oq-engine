Classical PSHA - Loss fractions QA test
=======================================

============== ===================
checksum32     177,006,542        
date           2018-06-05T06:38:11
engine_version 3.2.0-git65c4735   
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
232       AreaSource   1,612        0.00807   0.03465    6.04839   124       0     
225       AreaSource   520          0.00522   0.01414    2.00000   18        0     
101       AreaSource   559          0.0       0.01904    0.0       0         0     
125       AreaSource   8,274        0.0       0.25210    0.0       0         0     
135       AreaSource   3,285        0.0       0.12146    0.0       0         0     
137       AreaSource   2,072        0.0       0.07391    0.0       0         0     
253       AreaSource   3,058        0.0       0.07666    0.0       0         0     
27        AreaSource   1,482        0.0       0.03766    0.0       0         0     
299       AreaSource   710          0.0       0.01677    0.0       0         0     
306       AreaSource   1,768        0.0       0.05994    0.0       0         0     
359       AreaSource   2,314        0.0       0.05938    0.0       0         0     
42        AreaSource   1,755        0.0       0.03550    0.0       0         0     
57        AreaSource   840          0.0       0.01629    0.0       0         0     
59        AreaSource   750          0.0       0.01691    0.0       0         0     
8         AreaSource   4,832        0.0       0.34206    0.0       0         0     
========= ============ ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
AreaSource   0.01329   15    
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =========
operation-duration mean    stddev  min     max     num_tasks
RtreeFilter        0.01641 0.00860 0.00382 0.03959 60       
count_eff_ruptures 0.01157 0.00492 0.00809 0.01505 2        
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

Data transfer
-------------
================== ======================================================================= ========
task               sent                                                                    received
RtreeFilter        srcs=603.23 KB monitor=20.27 KB srcfilter=16.35 KB                      40.92 KB
count_eff_ruptures sources=39.19 KB param=1.1 KB monitor=706 B srcfilter=466 B gsims=254 B 791 B   
================== ======================================================================= ========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
ClassicalCalculator.run        2.94878   6.47266   1     
PSHACalculator.run             2.90333   5.24609   1     
splitting sources              1.17832   1.35938   1     
reading composite source model 1.16371   0.69141   1     
total prefilter                0.98490   3.13672   60    
managing sources               0.40370   1.28125   1     
unpickling prefilter           0.02412   0.14844   60    
total count_eff_ruptures       0.02314   6.50000   2     
store source_info              0.00521   0.86328   1     
reading site collection        0.00282   0.05469   1     
reading exposure               0.00157   0.13672   1     
aggregate curves               5.040E-04 0.0       2     
unpickling count_eff_ruptures  4.795E-04 0.0       2     
saving probability maps        2.394E-04 0.0       1     
============================== ========= ========= ======