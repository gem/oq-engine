Classical BCR test
==================

============== ===================
checksum32     1,808,877,325      
date           2018-05-15T04:13:04
engine_version 3.1.0-git0acbc11   
============== ===================

num_sites = 11, num_levels = 8

Parameters
----------
=============================== ==================
calculation_mode                'classical_bcr'   
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              50.0              
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            20.0              
complex_fault_mesh_spacing      20.0              
width_of_mfd_bin                0.5               
area_source_discretization      20.0              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     42                
master_seed                     0                 
ses_seed                        42                
=============================== ==================

Input files
-----------
==================================== ============================================================================
Name                                 File                                                                        
==================================== ============================================================================
exposure                             `exposure_model.xml <exposure_model.xml>`_                                  
gsim_logic_tree                      `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                                
job_ini                              `job.ini <job.ini>`_                                                        
source                               `source_model.xml <source_model.xml>`_                                      
source_model_logic_tree              `source_model_logic_tree.xml <source_model_logic_tree.xml>`_                
structural_vulnerability             `structural_vulnerability_model.xml <structural_vulnerability_model.xml>`_  
structural_vulnerability_retrofitted `vulnerability_model_retrofitted.xml <vulnerability_model_retrofitted.xml>`_
==================================== ============================================================================

Composite source model
----------------------
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
b1        1.00000 simple(3)       3/3             
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ======================================================= =========== ======================= =================
grp_id gsims                                                   distances   siteparams              ruptparams       
====== ======================================================= =========== ======================= =================
0      AkkarBommer2010() BooreAtkinson2008() ChiouYoungs2008() rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
====== ======================================================= =========== ======================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=3, rlzs=3)
  0,AkkarBommer2010(): [2]
  0,BooreAtkinson2008(): [1]
  0,ChiouYoungs2008(): [0]>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== ============ ============
source_model     grp_id trt                  eff_ruptures tot_ruptures
================ ====== ==================== ============ ============
source_model.xml 0      Active Shallow Crust 792          828         
================ ====== ==================== ============ ============

Exposure model
--------------
=============== ========
#assets         11      
#taxonomies     4       
deductibile     absolute
insurance_limit absolute
=============== ========

========================== ======= ====== === === ========= ==========
taxonomy                   mean    stddev min max num_sites num_assets
Adobe                      1.00000 0.0    1   1   2         2         
Stone-Masonry              1.00000 0.0    1   1   6         6         
Unreinforced-Brick-Masonry 1.00000 NaN    1   1   1         1         
Wood                       1.00000 0.0    1   1   2         2         
*ALL*                      1.00000 0.0    1   1   11        11        
========================== ======= ====== === === ========= ==========

Slowest sources
---------------
========= ============ ============ ========= ========== ========= ========= ======
source_id source_class num_ruptures calc_time split_time num_sites num_split events
========= ============ ============ ========= ========== ========= ========= ======
229       AreaSource   264          8.821E-04 0.01606    203       38        0     
231       AreaSource   414          8.669E-04 0.02140    697       69        0     
232       AreaSource   150          3.934E-04 0.01153    270       30        0     
========= ============ ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
AreaSource   0.00214   3     
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =========
operation-duration mean    stddev  min     max     num_tasks
prefilter          0.00495 0.00354 0.00120 0.02146 48       
count_ruptures     0.00357 0.00256 0.00106 0.00617 3        
================== ======= ======= ======= ======= =========

Fastest task
------------
taskno=3, weight=22, duration=0 s, sources="232"

======== ======= ======= ======= ======= =
variable mean    stddev  min     max     n
======== ======= ======= ======= ======= =
nsites   9.20000 1.30384 8       11      5
weight   4.54073 0.31976 4.24264 4.97494 5
======== ======= ======= ======= ======= =

Slowest task
------------
taskno=1, weight=328, duration=0 s, sources="229 231"

======== ======= ======= ======= ======= ==
variable mean    stddev  min     max     n 
======== ======= ======= ======= ======= ==
nsites   7.66176 3.22588 1       11      68
weight   4.82933 1.23456 1.80000 5.96992 68
======== ======= ======= ======= ======= ==

Informational data
------------------
============== ========================================================================== ========
task           sent                                                                       received
prefilter      srcs=77.11 KB monitor=15.28 KB srcfilter=10.73 KB                          87.33 KB
count_ruptures sources=50.88 KB srcfilter=3.69 KB param=1.32 KB monitor=999 B gsims=924 B 1.19 KB 
============== ========================================================================== ========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total prefilter                0.23775   3.43359   48    
managing sources               0.20873   0.0       1     
reading composite source model 0.05440   0.0       1     
splitting sources              0.04960   0.0       1     
total count_ruptures           0.01070   0.27734   3     
unpickling prefilter           0.00649   0.0       48    
reading site collection        0.00423   0.0       1     
store source_info              0.00418   0.0       1     
reading exposure               0.00163   0.0       1     
unpickling count_ruptures      1.180E-04 0.0       3     
aggregate curves               6.771E-05 0.0       3     
saving probability maps        3.433E-05 0.0       1     
============================== ========= ========= ======