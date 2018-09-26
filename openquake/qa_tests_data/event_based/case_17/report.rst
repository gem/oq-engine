Event Based Hazard QA Test, Case 17
===================================

============== ===================
checksum32     2,756,942,605      
date           2018-09-25T14:28:03
engine_version 3.3.0-git8ffb37de56
============== ===================

num_sites = 1, num_levels = 3

Parameters
----------
=============================== ==================
calculation_mode                'event_based'     
number_of_logic_tree_samples    5                 
maximum_distance                {'default': 200.0}
investigation_time              1.0               
ses_per_logic_tree_path         3                 
truncation_level                2.0               
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                1.0               
area_source_discretization      20.0              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     106               
master_seed                     0                 
ses_seed                        106               
=============================== ==================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gsim_logic_tree.xml <gsim_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
source                  `source_model_1.xml <source_model_1.xml>`_                  
source                  `source_model_2.xml <source_model_2.xml>`_                  
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
b1        0.20000 trivial(1)      3/1             
b2        0.20000 trivial(1)      2/1             
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================ ========= ========== ==========
grp_id gsims            distances siteparams ruptparams
====== ================ ========= ========== ==========
0      SadighEtAl1997() rrup      vs30       mag rake  
1      SadighEtAl1997() rrup      vs30       mag rake  
====== ================ ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=2, rlzs=5)
  0,SadighEtAl1997(): [0 1 2]
  1,SadighEtAl1997(): [3 4]>

Number of ruptures per tectonic region type
-------------------------------------------
================== ====== ==================== ============ ============
source_model       grp_id trt                  eff_ruptures tot_ruptures
================== ====== ==================== ============ ============
source_model_1.xml 0      Active Shallow Crust 39           39          
source_model_2.xml 1      Active Shallow Crust 7            7           
================== ====== ==================== ============ ============

============= ==
#TRT models   2 
#eff_ruptures 46
#tot_ruptures 46
#tot_weight   0 
============= ==

Slowest sources
---------------
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======
grp_id source_id code gidx1 gidx2 num_ruptures calc_time split_time num_sites num_split weight
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======
0      1         P    0     1     39           0.02511   1.621E-05  1.00000   1         0.0   
1      2         P    0     1     7            0.01025   4.768E-06  1.00000   1         13    
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
P    0.03536   2     
==== ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ========= ======= ======= =========
operation-duration mean    stddev    min     max     num_tasks
read_source_models 0.00197 8.708E-04 0.00136 0.00259 2        
split_filter       0.00341 NaN       0.00341 0.00341 1        
build_ruptures     0.02249 0.01046   0.01510 0.02989 2        
================== ======= ========= ======= ======= =========

Data transfer
-------------
================== ====================================================================== ========
task               sent                                                                   received
read_source_models monitor=662 B converter=638 B fnames=372 B                             3.36 KB 
split_filter       srcs=2.1 KB monitor=343 B srcfilter=220 B sample_factor=21 B seed=14 B 2.18 KB 
build_ruptures     srcs=3.17 KB monitor=690 B param=576 B srcfilter=440 B                 6.86 KB 
================== ====================================================================== ========

Slowest operations
------------------
======================== ======== ========= ======
operation                time_sec memory_mb counts
======================== ======== ========= ======
total build_ruptures     0.04499  0.0       2     
updating source_info     0.01242  0.0       1     
saving ruptures          0.00610  0.0       1     
store source_info        0.00567  0.0       1     
total read_source_models 0.00394  0.0       2     
total split_filter       0.00341  0.0       1     
making contexts          0.00149  0.0       3     
======================== ======== ========= ======