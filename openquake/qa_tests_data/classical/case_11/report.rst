Classical Hazard QA Test, Case 11
=================================

============== ===================
checksum32     3,151,174,296      
date           2018-05-15T04:13:31
engine_version 3.1.0-git0acbc11   
============== ===================

num_sites = 1, num_levels = 4

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
complex_fault_mesh_spacing      0.01              
width_of_mfd_bin                0.001             
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
b1_b2     0.20000 trivial(1)      1/1             
b1_b3     0.60000 trivial(1)      1/1             
b1_b4     0.20000 trivial(1)      1/1             
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================ ========= ========== ==========
grp_id gsims            distances siteparams ruptparams
====== ================ ========= ========== ==========
0      SadighEtAl1997() rjb rrup  vs30       mag rake  
1      SadighEtAl1997() rjb rrup  vs30       mag rake  
2      SadighEtAl1997() rjb rrup  vs30       mag rake  
====== ================ ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=3, rlzs=3)
  0,SadighEtAl1997(): [0]
  1,SadighEtAl1997(): [1]
  2,SadighEtAl1997(): [2]>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== ============ ============
source_model     grp_id trt                  eff_ruptures tot_ruptures
================ ====== ==================== ============ ============
source_model.xml 0      Active Shallow Crust 3,500        3,000       
source_model.xml 1      Active Shallow Crust 3,000        3,000       
source_model.xml 2      Active Shallow Crust 2,500        3,000       
================ ====== ==================== ============ ============

============= =====
#TRT models   3    
#eff_ruptures 9,000
#tot_ruptures 9,000
#tot_weight   900  
============= =====

Slowest sources
---------------
========= ============ ============ ========= ========== ========= ========= ======
source_id source_class num_ruptures calc_time split_time num_sites num_split events
========= ============ ============ ========= ========== ========= ========= ======
1         PointSource  2,500        1.476E-04 1.431E-06  3         3         0     
========= ============ ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
PointSource  1.476E-04 1     
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ========= ======= ======= =========
operation-duration mean    stddev    min     max     num_tasks
prefilter          0.00873 8.447E-04 0.00776 0.00932 3        
count_ruptures     0.00213 5.424E-04 0.00154 0.00261 3        
================== ======= ========= ======= ======= =========

Fastest task
------------
taskno=1, weight=350, duration=0 s, sources="1"

======== ======= ====== === === =
variable mean    stddev min max n
======== ======= ====== === === =
nsites   1.00000 NaN    1   1   1
weight   350     NaN    350 350 1
======== ======= ====== === === =

Slowest task
------------
taskno=3, weight=250, duration=0 s, sources="1"

======== ======= ====== === === =
variable mean    stddev min max n
======== ======= ====== === === =
nsites   1.00000 NaN    1   1   1
weight   250     NaN    250 250 1
======== ======= ====== === === =

Informational data
------------------
============== ======================================================================= ========
task           sent                                                                    received
prefilter      srcs=3.42 KB monitor=978 B srcfilter=687 B                              3.76 KB 
count_ruptures sources=3.9 KB srcfilter=2.1 KB param=1.23 KB monitor=999 B gsims=360 B 1.05 KB 
============== ======================================================================= ========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total prefilter                0.02618   2.93359   3     
managing sources               0.02290   0.0       1     
reading composite source model 0.01899   0.0       1     
total count_ruptures           0.00640   1.68359   3     
store source_info              0.00354   0.0       1     
splitting sources              4.396E-04 0.0       1     
reading site collection        2.751E-04 0.0       1     
unpickling prefilter           2.201E-04 0.0       3     
unpickling count_ruptures      1.004E-04 0.0       3     
aggregate curves               5.674E-05 0.0       3     
saving probability maps        2.813E-05 0.0       1     
============================== ========= ========= ======