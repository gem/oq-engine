Classical PSHA — Area Source
============================

============== ===================
checksum32     3,283,112,543      
date           2018-05-15T04:13:30
engine_version 3.1.0-git0acbc11   
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
1         AreaSource   11,132       0.00729   0.07973    484       484       0     
========= ============ ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
AreaSource   0.00729   1     
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =========
operation-duration mean    stddev  min     max     num_tasks
prefilter          0.00676 0.00307 0.00236 0.01335 54       
count_ruptures     0.00977 0.00556 0.00434 0.01471 4        
================== ======= ======= ======= ======= =========

Fastest task
------------
taskno=3, weight=278, duration=0 s, sources="1"

======== ======= ========= ======= ======= ===
variable mean    stddev    min     max     n  
======== ======= ========= ======= ======= ===
nsites   1.00000 0.0       1       1       121
weight   2.30000 2.394E-07 2.30000 2.30000 121
======== ======= ========= ======= ======= ===

Slowest task
------------
taskno=4, weight=278, duration=0 s, sources="1"

======== ======= ========= ======= ======= ===
variable mean    stddev    min     max     n  
======== ======= ========= ======= ======= ===
nsites   1.00000 0.0       1       1       121
weight   2.30000 2.394E-07 2.30000 2.30000 121
======== ======= ========= ======= ======= ===

Informational data
------------------
============== =========================================================================== =========
task           sent                                                                        received 
prefilter      srcs=145.14 KB monitor=17.19 KB srcfilter=12.08 KB                          167.37 KB
count_ruptures sources=134.34 KB srcfilter=2.8 KB param=2.13 KB monitor=1.3 KB gsims=524 B 1.4 KB   
============== =========================================================================== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total prefilter                0.36482   3.37109   54    
managing sources               0.21149   0.0       1     
splitting sources              0.08054   0.0       1     
reading composite source model 0.05650   0.0       1     
total count_ruptures           0.03908   0.0       4     
unpickling prefilter           0.00947   0.0       54    
store source_info              0.00349   0.0       1     
reading site collection        3.018E-04 0.0       1     
unpickling count_ruptures      1.445E-04 0.0       4     
aggregate curves               7.033E-05 0.0       4     
saving probability maps        3.147E-05 0.0       1     
============================== ========= ========= ======