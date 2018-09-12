Classical PSHA using Area Source
================================

============== ===================
checksum32     1,839,663,514      
date           2018-09-05T10:04:38
engine_version 3.2.0-gitb4ef3a4b6c
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
1         AreaSource   260          0.00330   0.01277    1.00000   52        0     
========= ============ ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
AreaSource   0.00330   1     
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
==================== ======= ========= ======= ======= =========
operation-duration   mean    stddev    min     max     num_tasks
pickle_source_models 0.01406 NaN       0.01406 0.01406 1        
count_eff_ruptures   0.00474 NaN       0.00474 0.00474 1        
preprocess           0.00254 6.064E-04 0.00144 0.00315 11       
==================== ======= ========= ======= ======= =========

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

Data transfer
-------------
==================== ======================================================================== ========
task                 sent                                                                     received
pickle_source_models monitor=0 B fnames=0 B converter=0 B                                     156 B   
count_eff_ruptures   sources=15.74 KB param=2.57 KB monitor=307 B srcfilter=220 B gsims=131 B 359 B   
preprocess           srcs=21.09 KB monitor=3.43 KB srcfilter=2.72 KB param=396 B              23.33 KB
==================== ======================================================================== ========

Slowest operations
------------------
========================== ========= ========= ======
operation                  time_sec  memory_mb counts
========================== ========= ========= ======
managing sources           0.04395   0.0       1     
total preprocess           0.02791   0.0       11    
total pickle_source_models 0.01406   0.0       1     
splitting sources          0.01309   0.0       1     
total count_eff_ruptures   0.00474   0.0       1     
store source_info          0.00386   0.0       1     
aggregate curves           1.945E-04 0.0       1     
========================== ========= ========= ======