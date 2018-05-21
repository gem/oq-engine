Classical PSHA using Area Source
================================

============== ===================
checksum32     1,839,663,514      
date           2018-05-15T04:13:10
engine_version 3.1.0-git0acbc11   
============== ===================

num_sites = 1, num_levels = 197

Parameters
----------
=============================== ==================
calculation_mode                'classical'       
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              50.0              
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            5.0               
complex_fault_mesh_spacing      5.0               
width_of_mfd_bin                0.3               
area_source_discretization      10.0              
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
source_model.xml 0      Active Shallow Crust 260          260         
================ ====== ==================== ============ ============

Slowest sources
---------------
========= ============ ============ ========= ========== ========= ========= ======
source_id source_class num_ruptures calc_time split_time num_sites num_split events
========= ============ ============ ========= ========== ========= ========= ======
1         AreaSource   260          6.242E-04 0.01763    52        52        0     
========= ============ ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
AreaSource   6.242E-04 1     
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =========
operation-duration mean    stddev  min     max     num_tasks
prefilter          0.00325 0.00177 0.00118 0.00706 52       
count_ruptures     0.00671 NaN     0.00671 0.00671 1        
================== ======= ======= ======= ======= =========

Fastest task
------------
taskno=1, weight=26, duration=0 s, sources="1"

======== ======= ====== ======= ======= ==
variable mean    stddev min     max     n 
======== ======= ====== ======= ======= ==
nsites   1.00000 0.0    1       1       52
weight   0.50000 0.0    0.50000 0.50000 52
======== ======= ====== ======= ======= ==

Slowest task
------------
taskno=1, weight=26, duration=0 s, sources="1"

======== ======= ====== ======= ======= ==
variable mean    stddev min     max     n 
======== ======= ====== ======= ======= ==
nsites   1.00000 0.0    1       1       52
weight   0.50000 0.0    0.50000 0.50000 52
======== ======= ====== ======= ======= ==

Informational data
------------------
============== ======================================================================== ========
task           sent                                                                     received
prefilter      srcs=64.69 KB monitor=16.55 KB srcfilter=11.63 KB                        68.7 KB 
count_ruptures sources=24.87 KB param=2.48 KB srcfilter=717 B monitor=333 B gsims=131 B 359 B   
============== ======================================================================== ========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
managing sources               0.18304   0.0       1     
total prefilter                0.16895   3.37109   52    
reading composite source model 0.02119   0.0       1     
splitting sources              0.01821   0.0       1     
total count_ruptures           0.00671   0.0       1     
unpickling prefilter           0.00476   0.0       52    
store source_info              0.00394   0.0       1     
reading site collection        3.145E-04 0.0       1     
unpickling count_ruptures      3.934E-05 0.0       1     
saving probability maps        3.362E-05 0.0       1     
aggregate curves               2.575E-05 0.0       1     
============================== ========= ========= ======