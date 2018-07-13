Classical Hazard QA Test, Case 12
=================================

============== ===================
checksum32     3,041,491,618      
date           2018-06-26T14:57:52
engine_version 3.2.0-gitb0cd949   
============== ===================

num_sites = 1, num_levels = 3

Parameters
----------
=============================== ==================
calculation_mode                'classical'       
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              1.0               
ses_per_logic_tree_path         1                 
truncation_level                2.0               
rupture_mesh_spacing            1.0               
complex_fault_mesh_spacing      1.0               
width_of_mfd_bin                1.0               
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
b1        1.00000 trivial(1,1)    1/1             
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== =================== ========= ========== ==========
grp_id gsims               distances siteparams ruptparams
====== =================== ========= ========== ==========
0      SadighEtAl1997()    rrup      vs30       mag rake  
1      BooreAtkinson2008() rjb       vs30       mag rake  
====== =================== ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=2, rlzs=1)
  0,SadighEtAl1997(): [0]
  1,BooreAtkinson2008(): [0]>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== ============ ============
source_model     grp_id trt                  eff_ruptures tot_ruptures
================ ====== ==================== ============ ============
source_model.xml 0      Active Shallow Crust 1            1           
source_model.xml 1      Stable Continental   1            1           
================ ====== ==================== ============ ============

============= =======
#TRT models   2      
#eff_ruptures 2      
#tot_ruptures 2      
#tot_weight   0.20000
============= =======

Slowest sources
---------------
========= ============ ============ ========= ========== ========= ========= ======
source_id source_class num_ruptures calc_time split_time num_sites num_split events
========= ============ ============ ========= ========== ========= ========= ======
2         PointSource  1            0.00628   1.192E-06  1.00000   1         0     
1         PointSource  1            0.00537   3.338E-06  1.00000   1         0     
========= ============ ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
PointSource  0.01165   2     
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ========= ======= ======= =========
operation-duration mean    stddev    min     max     num_tasks
RtreeFilter        0.00234 4.193E-04 0.00205 0.00264 2        
count_eff_ruptures 0.00731 8.472E-04 0.00671 0.00791 2        
================== ======= ========= ======= ======= =========

Fastest task
------------
taskno=1, weight=0, duration=0 s, sources="1"

======== ======= ====== ======= ======= =
variable mean    stddev min     max     n
======== ======= ====== ======= ======= =
nsites   1.00000 NaN    1       1       1
weight   0.10000 NaN    0.10000 0.10000 1
======== ======= ====== ======= ======= =

Slowest task
------------
taskno=2, weight=0, duration=0 s, sources="2"

======== ======= ====== ======= ======= =
variable mean    stddev min     max     n
======== ======= ====== ======= ======= =
nsites   1.00000 NaN    1       1       1
weight   0.10000 NaN    0.10000 0.10000 1
======== ======= ====== ======= ======= =

Data transfer
-------------
================== ===================================================================== ========
task               sent                                                                  received
RtreeFilter        srcs=2.26 KB monitor=644 B srcfilter=558 B                            2.49 KB 
count_eff_ruptures sources=2.58 KB param=862 B monitor=658 B srcfilter=492 B gsims=251 B 716 B   
================== ===================================================================== ========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
managing sources               0.17894   0.0       1     
total count_eff_ruptures       0.01462   6.81250   2     
store source_info              0.00552   0.0       1     
total prefilter                0.00468   1.64453   2     
reading composite source model 0.00240   0.0       1     
unpickling prefilter           5.071E-04 0.0       2     
unpickling count_eff_ruptures  4.368E-04 0.0       2     
aggregate curves               4.172E-04 0.0       2     
reading site collection        2.985E-04 0.0       1     
splitting sources              2.403E-04 0.0       1     
============================== ========= ========= ======