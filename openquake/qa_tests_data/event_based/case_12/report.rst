Event Based QA Test, Case 12
============================

============== ===================
checksum32     1,316,139,513      
date           2018-09-25T14:28:09
engine_version 3.3.0-git8ffb37de56
============== ===================

num_sites = 1, num_levels = 3

Parameters
----------
=============================== ==================
calculation_mode                'event_based'     
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              1.0               
ses_per_logic_tree_path         3500              
truncation_level                2.0               
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                1.0               
area_source_discretization      20.0              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     42                
master_seed                     0                 
ses_seed                        1066              
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
b1        1.00000 trivial(1,1)    1/1             
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== =================== ========= ========== ==========
grp_id gsims               distances siteparams ruptparams
====== =================== ========= ========== ==========
0      SadighEtAl1997()    rrup      vs30       mag rake  
1      BooreAtkinson2008() rjb       vs30       mag rake  
====== =================== ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=2, rlzs=1)
  0,SadighEtAl1997(): [0]
  1,BooreAtkinson2008(): [0]>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== ============ ============
source_model     grp_id trt                  eff_ruptures tot_ruptures
================ ====== ==================== ============ ============
source_model.xml 0      Active Shallow Crust 1            1           
source_model.xml 1      Stable Continental   1            1           
================ ====== ==================== ============ ============

============= =
#TRT models   2
#eff_ruptures 2
#tot_ruptures 2
#tot_weight   0
============= =

Slowest sources
---------------
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======
grp_id source_id code gidx1 gidx2 num_ruptures calc_time split_time num_sites num_split weight
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======
0      1         P    0     1     1            0.02202   1.335E-05  1.00000   1         3,536 
1      2         P    1     2     1            0.02112   3.338E-06  1.00000   1         3,370 
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
P    0.04314   2     
==== ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ========= ======= ======= =========
operation-duration mean    stddev    min     max     num_tasks
read_source_models 0.00119 NaN       0.00119 0.00119 1        
split_filter       0.00316 NaN       0.00316 0.00316 1        
build_ruptures     0.02461 5.225E-04 0.02424 0.02498 2        
================== ======= ========= ======= ======= =========

Data transfer
-------------
================== ======================================================================= =========
task               sent                                                                    received 
read_source_models monitor=0 B fnames=0 B converter=0 B                                    1.94 KB  
split_filter       srcs=1.62 KB monitor=432 B srcfilter=220 B sample_factor=21 B seed=14 B 1.71 KB  
build_ruptures     srcs=2.71 KB param=812 B monitor=690 B srcfilter=440 B                  127.46 KB
================== ======================================================================= =========

Slowest operations
------------------
======================== ========= ========= ======
operation                time_sec  memory_mb counts
======================== ========= ========= ======
total build_ruptures     0.04923   0.25391   2     
saving ruptures          0.03594   0.0       2     
updating source_info     0.00860   0.0       1     
store source_info        0.00566   0.0       1     
total split_filter       0.00316   0.25391   1     
total read_source_models 0.00119   0.0       1     
making contexts          7.420E-04 0.0       2     
======================== ========= ========= ======