Classical Hazard QA Test, Case 9
================================

============== ===================
checksum32     1,375,199,152      
date           2018-06-26T14:57:29
engine_version 3.2.0-gitb0cd949   
============== ===================

num_sites = 1, num_levels = 4

Parameters
----------
=============================== ==================
calculation_mode                'classical'       
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              1.0               
ses_per_logic_tree_path         1                 
truncation_level                0.0               
rupture_mesh_spacing            0.01              
complex_fault_mesh_spacing      0.01              
width_of_mfd_bin                0.001             
area_source_discretization      10.0              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     1066              
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
source                  `source_model.xml <source_model.xml>`_                      
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
b1_b2     0.50000 trivial(1)      1/1             
b1_b3     0.50000 trivial(1)      1/1             
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

  <RlzsAssoc(size=2, rlzs=2)
  0,SadighEtAl1997(): [0]
  1,SadighEtAl1997(): [1]>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== ============ ============
source_model     grp_id trt                  eff_ruptures tot_ruptures
================ ====== ==================== ============ ============
source_model.xml 0      Active Shallow Crust 3,000        3,000       
source_model.xml 1      Active Shallow Crust 3,500        3,000       
================ ====== ==================== ============ ============

============= =====
#TRT models   2    
#eff_ruptures 6,500
#tot_ruptures 6,000
#tot_weight   650  
============= =====

Slowest sources
---------------
========= ============ ============ ========= ========== ========= ========= ======
source_id source_class num_ruptures calc_time split_time num_sites num_split events
========= ============ ============ ========= ========== ========= ========= ======
1         PointSource  3,500        0.00959   1.907E-06  1.00000   2         0     
========= ============ ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
PointSource  0.00959   1     
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ========= ======= ======= =========
operation-duration mean    stddev    min     max     num_tasks
RtreeFilter        0.01442 0.00199   0.01302 0.01583 2        
count_eff_ruptures 0.00638 8.490E-04 0.00578 0.00698 2        
================== ======= ========= ======= ======= =========

Fastest task
------------
taskno=1, weight=300, duration=0 s, sources="1"

======== ======= ====== === === =
variable mean    stddev min max n
======== ======= ====== === === =
nsites   1.00000 NaN    1   1   1
weight   300     NaN    300 300 1
======== ======= ====== === === =

Slowest task
------------
taskno=2, weight=350, duration=0 s, sources="1"

======== ======= ====== === === =
variable mean    stddev min max n
======== ======= ====== === === =
nsites   1.00000 NaN    1   1   1
weight   350     NaN    350 350 1
======== ======= ====== === === =

Data transfer
-------------
================== ==================================================================== ========
task               sent                                                                 received
RtreeFilter        srcs=2.28 KB monitor=644 B srcfilter=558 B                           2.51 KB 
count_eff_ruptures sources=2.6 KB param=878 B monitor=658 B srcfilter=492 B gsims=240 B 718 B   
================== ==================================================================== ========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
managing sources               0.10815   0.0       1     
total prefilter                0.02885   2.69141   2     
reading composite source model 0.01685   0.0       1     
total count_eff_ruptures       0.01277   6.33594   2     
store source_info              0.00626   0.0       1     
aggregate curves               6.382E-04 0.0       2     
unpickling prefilter           5.460E-04 0.0       2     
unpickling count_eff_ruptures  5.085E-04 0.0       2     
reading site collection        3.519E-04 0.0       1     
splitting sources              2.975E-04 0.0       1     
============================== ========= ========= ======