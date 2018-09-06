Classical PSHA — Area Source
============================

============== ===================
checksum32     3,283,112,543      
date           2018-09-05T10:04:30
engine_version 3.2.0-gitb4ef3a4b6c
============== ===================

num_sites = 1, num_levels = 19

Parameters
----------
=============================== ==================
calculation_mode                'classical'       
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              50.0              
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                0.2               
area_source_discretization      5.0               
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     23                
master_seed                     0                 
ses_seed                        42                
=============================== ==================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
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
====== =================== ========= ========== ==========
grp_id gsims               distances siteparams ruptparams
====== =================== ========= ========== ==========
0      BooreAtkinson2008() rjb       vs30       mag rake  
====== =================== ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)
  0,BooreAtkinson2008(): [0]>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== ============ ============
source_model     grp_id trt                  eff_ruptures tot_ruptures
================ ====== ==================== ============ ============
source_model.xml 0      Active Shallow Crust 11,132       11,132      
================ ====== ==================== ============ ============

Slowest sources
---------------
========= ============ ============ ========= ========== ========= ========= ======
source_id source_class num_ruptures calc_time split_time num_sites num_split events
========= ============ ============ ========= ========== ========= ========= ======
1         AreaSource   11,132       0.02833   0.06510    1.00000   484       0     
========= ============ ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
AreaSource   0.02833   1     
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
==================== ======= ========= ======= ======= =========
operation-duration   mean    stddev    min     max     num_tasks
pickle_source_models 0.04361 NaN       0.04361 0.04361 1        
count_eff_ruptures   0.00983 9.582E-04 0.00841 0.01053 4        
preprocess           0.02157 8.196E-04 0.02083 0.02274 4        
==================== ======= ========= ======= ======= =========

Fastest task
------------
taskno=1, weight=278, duration=0 s, sources="1"

======== ======= ========= ======= ======= ===
variable mean    stddev    min     max     n  
======== ======= ========= ======= ======= ===
nsites   1.00000 0.0       1       1       121
weight   2.30000 2.394E-07 2.30000 2.30000 121
======== ======= ========= ======= ======= ===

Slowest task
------------
taskno=2, weight=278, duration=0 s, sources="1"

======== ======= ========= ======= ======= ===
variable mean    stddev    min     max     n  
======== ======= ========= ======= ======= ===
nsites   1.00000 0.0       1       1       121
weight   2.30000 2.394E-07 2.30000 2.30000 121
======== ======= ========= ======= ======= ===

Data transfer
-------------
==================== ========================================================================= =========
task                 sent                                                                      received 
pickle_source_models monitor=0 B fnames=0 B converter=0 B                                      156 B    
count_eff_ruptures   sources=118.28 KB param=2.5 KB monitor=1.2 KB srcfilter=880 B gsims=524 B 1.4 KB   
preprocess           srcs=90.91 KB monitor=1.25 KB srcfilter=1012 B param=144 B                111.25 KB
==================== ========================================================================= =========

Slowest operations
------------------
========================== ======== ========= ======
operation                  time_sec memory_mb counts
========================== ======== ========= ======
total preprocess           0.08630  2.57422   4     
managing sources           0.07084  0.0       1     
splitting sources          0.06574  0.0       1     
total pickle_source_models 0.04361  0.0       1     
total count_eff_ruptures   0.03930  5.62500   4     
store source_info          0.00459  0.0       1     
aggregate curves           0.00127  0.0       4     
========================== ======== ========= ======