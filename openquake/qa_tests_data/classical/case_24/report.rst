Classical PSHA using Area Source
================================

============== ===================
checksum32     1,839,663,514      
date           2018-06-05T06:38:51
engine_version 3.2.0-git65c4735   
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
1         AreaSource   260          0.00439   0.01737    1.00000   52        0     
========= ============ ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
AreaSource   0.00439   1     
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ======= ========= ======= =========
operation-duration mean    stddev  min       max     num_tasks
RtreeFilter        0.00337 0.00198 9.792E-04 0.01071 52       
count_eff_ruptures 0.00867 NaN     0.00867   0.00867 1        
================== ======= ======= ========= ======= =========

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
================== ======================================================================= ========
task               sent                                                                    received
RtreeFilter        srcs=64.69 KB monitor=17.57 KB srcfilter=14.17 KB                       68.7 KB 
count_eff_ruptures sources=24.87 KB param=2.5 KB monitor=353 B srcfilter=233 B gsims=131 B 359 B   
================== ======================================================================= ========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
PSHACalculator.run             0.56216   0.0       1     
managing sources               0.35411   0.0       1     
total prefilter                0.17545   3.46875   52    
reading composite source model 0.02136   0.0       1     
unpickling prefilter           0.01873   0.0       52    
splitting sources              0.01777   0.0       1     
total count_eff_ruptures       0.00867   5.60547   1     
store source_info              0.00697   0.0       1     
reading site collection        8.657E-04 0.0       1     
unpickling count_eff_ruptures  3.057E-04 0.0       1     
aggregate curves               2.940E-04 0.0       1     
saving probability maps        2.613E-04 0.0       1     
============================== ========= ========= ======