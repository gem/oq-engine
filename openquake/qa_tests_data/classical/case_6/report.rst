Classical Hazard QA Test, Case 6
================================

============== ===================
checksum32     3,056,992,103      
date           2018-09-05T10:04:31
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
rupture_mesh_spacing            0.1               
complex_fault_mesh_spacing      0.1               
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
source_model.xml 0      Active Shallow Crust 140          140         
================ ====== ==================== ============ ============

Slowest sources
---------------
========= ================== ============ ========= ========== ========= ========= ======
source_id source_class       num_ruptures calc_time split_time num_sites num_split events
========= ================== ============ ========= ========== ========= ========= ======
1         SimpleFaultSource  91           0.00668   7.629E-06  1.00000   1         0     
2         ComplexFaultSource 49           0.00654   2.146E-06  1.00000   1         0     
========= ================== ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
================== ========= ======
source_class       calc_time counts
================== ========= ======
ComplexFaultSource 0.00654   1     
SimpleFaultSource  0.00668   1     
================== ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
==================== ======= ========= ======= ======= =========
operation-duration   mean    stddev    min     max     num_tasks
pickle_source_models 0.12447 NaN       0.12447 0.12447 1        
count_eff_ruptures   0.00747 9.323E-05 0.00740 0.00753 2        
preprocess           0.00406 6.840E-04 0.00357 0.00454 2        
==================== ======= ========= ======= ======= =========

Fastest task
------------
taskno=2, weight=196, duration=0 s, sources="2"

======== ======= ====== === === =
variable mean    stddev min max n
======== ======= ====== === === =
nsites   1.00000 NaN    1   1   1
weight   196     NaN    196 196 1
======== ======= ====== === === =

Slowest task
------------
taskno=1, weight=91, duration=0 s, sources="1"

======== ======= ====== === === =
variable mean    stddev min max n
======== ======= ====== === === =
nsites   1.00000 NaN    1   1   1
weight   91      NaN    91  91  1
======== ======= ====== === === =

Data transfer
-------------
==================== ====================================================================== ========
task                 sent                                                                   received
pickle_source_models monitor=0 B fnames=0 B converter=0 B                                   155 B   
count_eff_ruptures   sources=2.51 KB param=1012 B monitor=614 B srcfilter=440 B gsims=240 B 716 B   
preprocess           srcs=2.2 KB monitor=638 B srcfilter=506 B param=72 B                   2.36 KB 
==================== ====================================================================== ========

Slowest operations
------------------
========================== ========= ========= ======
operation                  time_sec  memory_mb counts
========================== ========= ========= ======
total pickle_source_models 0.12447   0.0       1     
managing sources           0.02308   0.0       1     
total count_eff_ruptures   0.01494   4.74609   2     
total preprocess           0.00811   0.87109   2     
store source_info          0.00553   0.0       1     
aggregate curves           5.293E-04 0.0       2     
splitting sources          2.379E-04 0.0       1     
========================== ========= ========= ======