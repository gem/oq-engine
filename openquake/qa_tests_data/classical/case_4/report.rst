Classical Hazard QA Test, Case 4
================================

============== ===================
checksum32     796,188,147        
date           2018-05-15T04:13:27
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
source_model.xml 0      Active Shallow Crust 91           91          
================ ====== ==================== ============ ============

Slowest sources
---------------
========= ================= ============ ========= ========== ========= ========= ======
source_id source_class      num_ruptures calc_time split_time num_sites num_split events
========= ================= ============ ========= ========== ========= ========= ======
1         SimpleFaultSource 91           4.554E-05 1.907E-05  1         1         0     
========= ================= ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
================= ========= ======
source_class      calc_time counts
================= ========= ======
SimpleFaultSource 4.554E-05 1     
================= ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ====== ======= ======= =========
operation-duration mean    stddev min     max     num_tasks
prefilter          0.00215 NaN    0.00215 0.00215 1        
count_ruptures     0.0     NaN    0.0     0.0     1        
================== ======= ====== ======= ======= =========

Fastest task
------------
taskno=1, weight=91, duration=0 s, sources="1"

======== ======= ====== === === =
variable mean    stddev min max n
======== ======= ====== === === =
nsites   1.00000 NaN    1   1   1
weight   91      NaN    91  91  1
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

Informational data
------------------
============== ===================================================================== ========
task           sent                                                                  received
prefilter      srcs=0 B srcfilter=0 B monitor=0 B                                    1.16 KB 
count_ruptures sources=1.21 KB srcfilter=717 B monitor=564 B param=412 B gsims=120 B 358 B   
============== ===================================================================== ========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
reading composite source model 0.03158   0.0       1     
managing sources               0.01019   0.0       1     
store source_info              0.00383   0.0       1     
total prefilter                0.00215   0.0       1     
total count_ruptures           0.00160   1.37109   1     
splitting sources              5.643E-04 0.0       1     
reading site collection        3.159E-04 0.0       1     
unpickling prefilter           9.036E-05 0.0       1     
unpickling count_ruptures      3.839E-05 0.0       1     
saving probability maps        3.457E-05 0.0       1     
aggregate curves               2.289E-05 0.0       1     
============================== ========= ========= ======