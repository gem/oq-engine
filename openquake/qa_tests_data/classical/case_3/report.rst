Classical Hazard QA Test, Case 3
================================

============== ===================
checksum32     4,051,148,706      
date           2018-05-15T04:13:13
engine_version 3.1.0-git0acbc11   
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
truncation_level                0.0               
rupture_mesh_spacing            1.0               
complex_fault_mesh_spacing      1.0               
width_of_mfd_bin                1.0               
area_source_discretization      0.05              
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
b1        1.00000 trivial(1)      1/1             
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================ ========= ========== ==========
grp_id gsims            distances siteparams ruptparams
====== ================ ========= ========== ==========
0      SadighEtAl1997() rjb rrup  vs30       mag rake  
====== ================ ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)
  0,SadighEtAl1997(): [0]>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== ============ ============
source_model     grp_id trt                  eff_ruptures tot_ruptures
================ ====== ==================== ============ ============
source_model.xml 0      Active Shallow Crust 31,353       31,353      
================ ====== ==================== ============ ============

Slowest sources
---------------
========= ============ ============ ========= ========== ========= ========= ======
source_id source_class num_ruptures calc_time split_time num_sites num_split events
========= ============ ============ ========= ========== ========= ========= ======
1         AreaSource   31,353       0.42048   5.33301    31,353    31,353    0     
========= ============ ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
AreaSource   0.42048   1     
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =========
operation-duration mean    stddev  min     max     num_tasks
prefilter          0.10376 0.03340 0.04792 0.19613 60       
count_ruptures     0.06144 0.02195 0.01295 0.09681 32       
================== ======= ======= ======= ======= =========

Fastest task
------------
taskno=32, weight=35, duration=0 s, sources="1"

======== ======= ========= ======= ======= ===
variable mean    stddev    min     max     n  
======== ======= ========= ======= ======= ===
nsites   1.00000 0.0       1       1       353
weight   0.10000 7.461E-09 0.10000 0.10000 353
======== ======= ========= ======= ======= ===

Slowest task
------------
taskno=1, weight=100, duration=0 s, sources="1"

======== ======= ========= ======= ======= ====
variable mean    stddev    min     max     n   
======== ======= ========= ======= ======= ====
nsites   1.00000 0.0       1       1       1000
weight   0.10000 1.491E-08 0.10000 0.10000 1000
======== ======= ========= ======= ======= ====

Informational data
------------------
============== ================================================================================ ========
task           sent                                                                             received
prefilter      srcs=5.46 MB monitor=19.16 KB srcfilter=13.42 KB                                 6.75 MB 
count_ruptures sources=7.22 MB srcfilter=22.41 KB param=12.88 KB monitor=10.41 KB gsims=3.75 KB 11.22 KB
============== ================================================================================ ========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total prefilter                6.22540   3.30859   60    
splitting sources              5.34909   7.23828   1     
reading composite source model 5.01801   0.0       1     
managing sources               1.98192   0.0       1     
total count_ruptures           1.96599   0.40234   32    
unpickling prefilter           0.51662   0.0       60    
store source_info              0.00390   0.0       1     
unpickling count_ruptures      0.00153   0.0       32    
aggregate curves               6.664E-04 0.0       32    
reading site collection        2.403E-04 0.0       1     
saving probability maps        3.266E-05 0.0       1     
============================== ========= ========= ======