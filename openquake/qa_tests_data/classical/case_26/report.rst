Classical PSHA — Area Source
============================

============== ===================
checksum32     3,283,112,543      
date           2018-04-30T11:22:11
engine_version 3.1.0-gitb0812f0   
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
1         AreaSource   11,132       0.00510   0.07810    484       484       0     
========= ============ ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
AreaSource   0.00510   1     
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ========= ======= ======= =========
operation-duration mean    stddev    min     max     num_tasks
count_ruptures     0.01051 1.689E-04 0.01036 0.01075 4        
================== ======= ========= ======= ======= =========

Fastest task
------------
taskno=4, weight=278, duration=0 s, sources="1"

======== ======= ========= ======= ======= ===
variable mean    stddev    min     max     n  
======== ======= ========= ======= ======= ===
nsites   1.00000 0.0       1       1       121
weight   2.30000 2.394E-07 2.30000 2.30000 121
======== ======= ========= ======= ======= ===

Slowest task
------------
taskno=1, weight=278, duration=0 s, sources="1"

======== ======= ========= ======= ======= ===
variable mean    stddev    min     max     n  
======== ======= ========= ======= ======= ===
nsites   1.00000 0.0       1       1       121
weight   2.30000 2.394E-07 2.30000 2.30000 121
======== ======= ========= ======= ======= ===

Informational data
------------------
============== ============================================================================ ========
task           sent                                                                         received
count_ruptures sources=111.53 KB srcfilter=2.8 KB param=2.13 KB monitor=1.29 KB gsims=524 B 1.4 KB  
============== ============================================================================ ========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
managing sources               0.08292   0.0       1     
splitting sources              0.07909   0.0       1     
reading composite source model 0.05340   0.0       1     
total count_ruptures           0.04203   1.84375   4     
store source_info              0.00390   0.0       1     
reading site collection        2.944E-04 0.0       1     
unpickling count_ruptures      1.657E-04 0.0       4     
aggregate curves               7.725E-05 0.0       4     
saving probability maps        3.386E-05 0.0       1     
============================== ========= ========= ======