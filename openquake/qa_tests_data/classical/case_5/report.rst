Classical Hazard QA Test, Case 5
================================

============== ===================
checksum32     2,343,185,032      
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
rupture_mesh_spacing            0.01              
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
source_model.xml 0      Active Shallow Crust 49           49          
================ ====== ==================== ============ ============

Slowest sources
---------------
========= ================== ============ ========= ========== ========= ========= ======
source_id source_class       num_ruptures calc_time split_time num_sites num_split events
========= ================== ============ ========= ========== ========= ========= ======
1         ComplexFaultSource 49           0.00654   7.868E-06  1.00000   1         0     
========= ================== ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
================== ========= ======
source_class       calc_time counts
================== ========= ======
ComplexFaultSource 0.00654   1     
================== ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
==================== ======= ====== ======= ======= =========
operation-duration   mean    stddev min     max     num_tasks
pickle_source_models 0.10202 NaN    0.10202 0.10202 1        
count_eff_ruptures   0.00739 NaN    0.00739 0.00739 1        
preprocess           0.00113 NaN    0.00113 0.00113 1        
==================== ======= ====== ======= ======= =========

Fastest task
------------
taskno=1, weight=196, duration=0 s, sources="1"

======== ======= ====== === === =
variable mean    stddev min max n
======== ======= ====== === === =
nsites   1.00000 NaN    1   1   1
weight   196     NaN    196 196 1
======== ======= ====== === === =

Slowest task
------------
taskno=1, weight=196, duration=0 s, sources="1"

======== ======= ====== === === =
variable mean    stddev min max n
======== ======= ====== === === =
nsites   1.00000 NaN    1   1   1
weight   196     NaN    196 196 1
======== ======= ====== === === =

Data transfer
-------------
==================== ===================================================================== ========
task                 sent                                                                  received
pickle_source_models monitor=0 B fnames=0 B converter=0 B                                  155 B   
count_eff_ruptures   sources=1.29 KB param=506 B monitor=307 B srcfilter=220 B gsims=120 B 358 B   
preprocess           srcs=0 B srcfilter=0 B param=0 B monitor=0 B                          1.22 KB 
==================== ===================================================================== ========

Slowest operations
------------------
========================== ========= ========= ======
operation                  time_sec  memory_mb counts
========================== ========= ========= ======
total pickle_source_models 0.10202   0.0       1     
managing sources           0.01017   0.0       1     
store source_info          0.00783   0.0       1     
total count_eff_ruptures   0.00739   4.72266   1     
total preprocess           0.00113   0.0       1     
aggregate curves           3.674E-04 0.0       1     
splitting sources          2.661E-04 0.0       1     
========================== ========= ========= ======