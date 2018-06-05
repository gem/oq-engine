Classical Hazard QA Test, Case 17
=================================

============== ===================
checksum32     575,048,364        
date           2018-06-05T06:38:44
engine_version 3.2.0-git65c4735   
============== ===================

num_sites = 1, num_levels = 3

Parameters
----------
=============================== ==================
calculation_mode                'classical'       
number_of_logic_tree_samples    5                 
maximum_distance                {'default': 200.0}
investigation_time              1000.0            
ses_per_logic_tree_path         1                 
truncation_level                2.0               
rupture_mesh_spacing            1.0               
complex_fault_mesh_spacing      1.0               
width_of_mfd_bin                1.0               
area_source_discretization      10.0              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     106               
master_seed                     0                 
ses_seed                        42                
=============================== ==================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gsim_logic_tree.xml <gsim_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
source                  `source_model_1.xml <source_model_1.xml>`_                  
source                  `source_model_2.xml <source_model_2.xml>`_                  
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
b1        0.20000 trivial(1)      3/1             
b2        0.20000 trivial(1)      2/1             
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================ ========= ========== ==========
grp_id gsims            distances siteparams ruptparams
====== ================ ========= ========== ==========
0      SadighEtAl1997() rrup      vs30       mag rake  
1      SadighEtAl1997() rrup      vs30       mag rake  
====== ================ ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=2, rlzs=5)
  0,SadighEtAl1997(): [0 1 2]
  1,SadighEtAl1997(): [3 4]>

Number of ruptures per tectonic region type
-------------------------------------------
================== ====== ==================== ============ ============
source_model       grp_id trt                  eff_ruptures tot_ruptures
================== ====== ==================== ============ ============
source_model_1.xml 0      Active Shallow Crust 46           39          
source_model_2.xml 1      Active Shallow Crust 46           7           
================== ====== ==================== ============ ============

============= =======
#TRT models   2      
#eff_ruptures 92     
#tot_ruptures 46     
#tot_weight   4.60000
============= =======

Slowest sources
---------------
========= ============ ============ ========= ========== ========= ========= ======
source_id source_class num_ruptures calc_time split_time num_sites num_split events
========= ============ ============ ========= ========== ========= ========= ======
1         PointSource  39           0.00440   9.060E-06  1.00000   2         0     
2         PointSource  7            3.409E-05 1.669E-06  1.00000   2         0     
========= ============ ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
PointSource  0.00443   2     
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =========
operation-duration mean    stddev  min     max     num_tasks
RtreeFilter        0.00340 0.00109 0.00263 0.00417 2        
count_eff_ruptures 0.00601 NaN     0.00601 0.00601 1        
================== ======= ======= ======= ======= =========

Fastest task
------------
taskno=1, weight=4, duration=0 s, sources="1 2"

======== ======= ======= ======= ======= =
variable mean    stddev  min     max     n
======== ======= ======= ======= ======= =
nsites   1.00000 0.0     1       1       2
weight   2.30000 2.26274 0.70000 3.90000 2
======== ======= ======= ======= ======= =

Slowest task
------------
taskno=1, weight=4, duration=0 s, sources="1 2"

======== ======= ======= ======= ======= =
variable mean    stddev  min     max     n
======== ======= ======= ======= ======= =
nsites   1.00000 0.0     1       1       2
weight   2.30000 2.26274 0.70000 3.90000 2
======== ======= ======= ======= ======= =

Data transfer
-------------
================== ===================================================================== ========
task               sent                                                                  received
RtreeFilter        srcs=2.52 KB monitor=692 B srcfilter=558 B                            2.76 KB 
count_eff_ruptures sources=1.98 KB param=431 B monitor=353 B srcfilter=233 B gsims=120 B 435 B   
================== ===================================================================== ========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
PSHACalculator.run             0.35141   0.0       1     
managing sources               0.16652   0.0       1     
store source_info              0.00747   0.0       1     
total prefilter                0.00680   2.85156   2     
reading composite source model 0.00640   0.0       1     
total count_eff_ruptures       0.00601   5.60547   1     
reading site collection        8.216E-04 0.0       1     
unpickling prefilter           5.658E-04 0.0       2     
splitting sources              3.645E-04 0.0       1     
aggregate curves               3.204E-04 0.0       1     
unpickling count_eff_ruptures  3.190E-04 0.0       1     
saving probability maps        2.451E-04 0.0       1     
============================== ========= ========= ======