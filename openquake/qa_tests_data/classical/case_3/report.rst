Classical Hazard QA Test, Case 3
================================

============== ===================
checksum32     4,051,148,706      
date           2018-09-05T10:04:41
engine_version 3.2.0-gitb4ef3a4b6c
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
0      SadighEtAl1997() rrup      vs30       mag rake  
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
1         AreaSource   31,353       0.37629   5.03350    1.00000   31,353    0     
========= ============ ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
AreaSource   0.37629   1     
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
==================== ======= ======= ======= ======= =========
operation-duration   mean    stddev  min     max     num_tasks
pickle_source_models 4.75508 NaN     4.75508 4.75508 1        
count_eff_ruptures   0.02832 0.00467 0.01230 0.03574 32       
preprocess           0.06921 0.00559 0.05679 0.08797 60       
==================== ======= ======= ======= ======= =========

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
taskno=19, weight=100, duration=0 s, sources="1"

======== ======= ========= ======= ======= ====
variable mean    stddev    min     max     n   
======== ======= ========= ======= ======= ====
nsites   1.00000 0.0       1       1       1000
weight   0.10000 1.491E-08 0.10000 0.10000 1000
======== ======= ========= ======= ======= ====

Data transfer
-------------
==================== ============================================================================== ========
task                 sent                                                                           received
pickle_source_models monitor=0 B fnames=0 B converter=0 B                                           155 B   
count_eff_ruptures   sources=7.34 MB param=15.81 KB monitor=9.59 KB srcfilter=6.88 KB gsims=3.75 KB 11.22 KB
preprocess           srcs=5.58 MB monitor=18.69 KB srcfilter=14.82 KB param=2.11 KB                 6.87 MB 
==================== ============================================================================== ========

Slowest operations
------------------
========================== ======== ========= ======
operation                  time_sec memory_mb counts
========================== ======== ========= ======
splitting sources          5.05225  3.88672   1     
total pickle_source_models 4.75508  0.0       1     
total preprocess           4.15238  0.0       60    
managing sources           1.70637  30        1     
total count_eff_ruptures   0.90639  0.0       32    
aggregate curves           0.00931  0.0       32    
store source_info          0.00490  0.0       1     
========================== ======== ========= ======