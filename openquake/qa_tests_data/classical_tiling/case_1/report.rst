Classical PSHA using Area Source
================================

============== ===================
checksum32     1,205,782,117      
date           2018-04-30T11:23:07
engine_version 3.1.0-gitb0812f0   
============== ===================

num_sites = 6, num_levels = 57

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
b1        1.00000 simple(2)       2/2             
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ===================================== =========== ======================= =================
grp_id gsims                                 distances   siteparams              ruptparams       
====== ===================================== =========== ======================= =================
0      BooreAtkinson2008() ChiouYoungs2008() rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
====== ===================================== =========== ======================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=2, rlzs=2)
  0,BooreAtkinson2008(): [0]
  0,ChiouYoungs2008(): [1]>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== ============ ============
source_model     grp_id trt                  eff_ruptures tot_ruptures
================ ====== ==================== ============ ============
source_model.xml 0      Active Shallow Crust 1,640        1,640       
================ ====== ==================== ============ ============

Slowest sources
---------------
========= ============ ============ ========= ========== ========= ========= ======
source_id source_class num_ruptures calc_time split_time num_sites num_split events
========= ============ ============ ========= ========== ========= ========= ======
1         AreaSource   1,640        0.01600   0.06328    1,230     1,230     0     
========= ============ ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
AreaSource   0.01600   1     
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =========
operation-duration mean    stddev  min     max     num_tasks
count_ruptures     0.01129 0.00555 0.00578 0.02060 12       
================== ======= ======= ======= ======= =========

Fastest task
------------
taskno=8, weight=83, duration=0 s, sources="1"

======== ======= ========= ======= ======= ==
variable mean    stddev    min     max     n 
======== ======= ========= ======= ======= ==
nsites   1.00000 0.0       1       1       52
weight   1.60000 1.204E-07 1.60000 1.60000 52
======== ======= ========= ======= ======= ==

Slowest task
------------
taskno=3, weight=244, duration=0 s, sources="1"

======== ======= ========= ======= ======= ===
variable mean    stddev    min     max     n  
======== ======= ========= ======= ======= ===
nsites   1.00000 0.0       1       1       153
weight   1.60000 2.392E-07 1.60000 1.60000 153
======== ======= ========= ======= ======= ===

Informational data
------------------
============== ================================================================================ ========
task           sent                                                                             received
count_ruptures sources=284.64 KB param=11.68 KB srcfilter=8.39 KB monitor=3.87 KB gsims=2.58 KB 4.21 KB 
============== ================================================================================ ========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total count_ruptures           0.13552   1.38281   12    
managing sources               0.13314   0.0       1     
reading composite source model 0.06414   0.0       1     
splitting sources              0.06393   0.0       1     
reading site collection        0.00445   0.0       1     
store source_info              0.00396   0.0       1     
unpickling count_ruptures      4.680E-04 0.0       12    
aggregate curves               2.038E-04 0.0       12    
saving probability maps        3.195E-05 0.0       1     
============================== ========= ========= ======