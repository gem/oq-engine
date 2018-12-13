Classical BCR test
==================

============== ===================
checksum32     1,808,877,325      
date           2018-12-13T12:57:03
engine_version 3.3.0-git68d7d11268
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
source_model.xml 0      Active Shallow Crust 744          828         
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
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======
grp_id source_id code gidx1 gidx2 num_ruptures calc_time split_time num_sites num_split weight
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======
0      229       A    0     4     264          0.31544   0.68416    203       38        50    
0      231       A    4     8     414          0.63448   0.99317    697       69        131   
0      232       A    8     12    150          0.22380   0.25180    270       30        44    
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
A    1.17372   3     
==== ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
read_source_models 0.04193 NaN     0.04193 0.04193 1      
split_filter       0.05656 NaN     0.05656 0.05656 1      
classical          0.39358 0.20571 0.15613 0.51760 3      
build_hazard_stats 0.00812 0.00349 0.00408 0.01374 11     
================== ======= ======= ======= ======= =======

Fastest task
------------
taskno=3, weight=29, duration=0 s, sources="232"

======== ======= ======= ======= ======= ==
variable mean    stddev  min     max     n 
======== ======= ======= ======= ======= ==
nsites   8.50000 1.14708 7       11      20
weight   1.45476 0.09554 1.32288 1.65831 20
======== ======= ======= ======= ======= ==

Slowest task
------------
taskno=3, weight=98, duration=0 s, sources="232"

======== ======= ======= ======= ======= ==
variable mean    stddev  min     max     n 
======== ======= ======= ======= ======= ==
nsites   8.50000 1.14708 7       11      20
weight   1.45476 0.09554 1.32288 1.65831 20
======== ======= ======= ======= ======= ==

Data transfer
-------------
================== =========================================================== ========
task               sent                                                        received
read_source_models converter=388 B fnames=110 B                                3.84 KB 
split_filter       srcs=3.49 KB srcfilter=253 B seed=14 B                      36.64 KB
classical          group=37.84 KB src_filter=3.83 KB param=1.48 KB gsims=924 B 9.44 KB 
build_hazard_stats pgetter=34.61 KB hstats=737 B                               4.59 KB 
================== =========================================================== ========

Slowest operations
------------------
======================== ========= ========= ======
operation                time_sec  memory_mb counts
======================== ========= ========= ======
total classical          1.18075   0.08984   3     
make_contexts            0.45725   0.0       792   
get_poes                 0.39985   0.0       744   
iter_ruptures            0.29260   0.0       137   
total build_hazard_stats 0.08931   0.53125   11    
combine pmaps            0.07870   0.53125   11    
total split_filter       0.05656   0.33984   1     
total read_source_models 0.04193   0.12500   1     
building riskinputs      0.02587   0.0       1     
store source_info        0.00898   0.0       3     
saving statistics        0.00674   0.0       11    
compute mean             0.00627   0.0       11    
managing sources         0.00501   0.16016   1     
store source model       0.00167   0.0       1     
saving probability maps  0.00124   0.0       1     
aggregate curves         0.00103   0.0       3     
reading exposure         4.447E-04 0.0       1     
======================== ========= ========= ======