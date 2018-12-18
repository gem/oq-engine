disaggregation with a complex logic tree
========================================

============== ===================
checksum32     1,766,748,636      
date           2018-12-13T12:57:08
engine_version 3.3.0-git68d7d11268
============== ===================

num_sites = 2, num_levels = 102

Parameters
----------
=============================== =================
calculation_mode                'disaggregation' 
number_of_logic_tree_samples    0                
maximum_distance                {'default': 60.0}
investigation_time              50.0             
ses_per_logic_tree_path         1                
truncation_level                3.0              
rupture_mesh_spacing            2.0              
complex_fault_mesh_spacing      2.0              
width_of_mfd_bin                0.1              
area_source_discretization      10.0             
ground_motion_correlation_model None             
minimum_intensity               {}               
random_seed                     24               
master_seed                     0                
ses_seed                        42               
=============================== =================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gsim_logic_tree.xml <gsim_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
b1        0.25000 complex(2,2)    4/4             
b2        0.75000 complex(2,2)    4/4             
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ===================================== =========== ======================= =================
grp_id gsims                                 distances   siteparams              ruptparams       
====== ===================================== =========== ======================= =================
0      BooreAtkinson2008() ChiouYoungs2008() rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
1      AkkarBommer2010() ChiouYoungs2008()   rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
2      BooreAtkinson2008() ChiouYoungs2008() rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
3      AkkarBommer2010() ChiouYoungs2008()   rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
====== ===================================== =========== ======================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=8, rlzs=8)
  0,BooreAtkinson2008(): [0 1]
  0,ChiouYoungs2008(): [2 3]
  1,AkkarBommer2010(): [0 2]
  1,ChiouYoungs2008(): [1 3]
  2,BooreAtkinson2008(): [4 5]
  2,ChiouYoungs2008(): [6 7]
  3,AkkarBommer2010(): [4 6]
  3,ChiouYoungs2008(): [5 7]>

Number of ruptures per tectonic region type
-------------------------------------------
================== ====== ==================== ============ ============
source_model       grp_id trt                  eff_ruptures tot_ruptures
================== ====== ==================== ============ ============
source_model_1.xml 0      Active Shallow Crust 543          543         
source_model_1.xml 1      Stable Shallow Crust 4            4           
source_model_2.xml 2      Active Shallow Crust 543          543         
source_model_2.xml 3      Stable Shallow Crust 1            1           
================== ====== ==================== ============ ============

============= =====
#TRT models   4    
#eff_ruptures 1,091
#tot_ruptures 1,091
#tot_weight   1,543
============= =====

Slowest sources
---------------
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= =======
grp_id source_id code gidx1 gidx2 num_ruptures calc_time split_time num_sites num_split weight 
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= =======
0      1         S    0     2     543          2.77108   0.00663    30        15        767    
1      2         S    2     4     4            0.01524   3.338E-05  2.00000   1         5.65685
2      1         S    0     2     543          2.75106   0.00442    30        15        767    
3      2         X    2     398   1            0.02847   9.775E-06  2.00000   1         1.41421
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= =======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
S    5.53738   3     
X    0.02847   1     
==== ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
read_source_models 0.01328 0.00289 0.01123 0.01532 2      
split_filter       0.05934 NaN     0.05934 0.05934 1      
classical          0.25375 0.08970 0.01570 0.38125 22     
build_hazard_stats 0.01233 0.00378 0.00965 0.01500 2      
================== ======= ======= ======= ======= =======

Fastest task
------------
taskno=22, weight=5, duration=0 s, sources="2"

======== ======= ====== ======= ======= =
variable mean    stddev min     max     n
======== ======= ====== ======= ======= =
nsites   2.00000 NaN    2       2       1
weight   1.41421 NaN    1.41421 1.41421 1
======== ======= ====== ======= ======= =

Slowest task
------------
taskno=22, weight=94, duration=0 s, sources="2"

======== ======= ====== ======= ======= =
variable mean    stddev min     max     n
======== ======= ====== ======= ======= =
nsites   2.00000 NaN    2       2       1
weight   1.41421 NaN    1.41421 1.41421 1
======== ======= ====== ======= ======= =

Data transfer
-------------
================== =============================================================== ========
task               sent                                                            received
read_source_models converter=776 B fnames=220 B                                    13.79 KB
split_filter       srcs=12.16 KB srcfilter=253 B seed=14 B                         18.23 KB
classical          group=37.64 KB param=28.75 KB src_filter=19.31 KB gsims=4.72 KB 84.03 KB
build_hazard_stats pgetter=8.96 KB hstats=402 B                                    5.89 KB 
================== =============================================================== ========

Slowest operations
------------------
======================== ========= ========= ======
operation                time_sec  memory_mb counts
======================== ========= ========= ======
total classical          5.58245   0.26953   22    
make_contexts            3.45065   0.0       1,091 
get_poes                 1.64695   0.0       1,091 
iter_ruptures            0.45209   0.0       32    
total split_filter       0.05934   0.12891   1     
store source_info        0.04960   0.0       22    
total read_source_models 0.02655   0.0       2     
total build_hazard_stats 0.02465   0.51562   2     
combine pmaps            0.01719   0.51562   2     
managing sources         0.00835   0.0       1     
store source model       0.00559   0.0       2     
aggregate curves         0.00555   0.0       22    
saving probability maps  0.00473   0.0       1     
compute quantile-0.15    0.00313   0.0       2     
compute quantile-0.85    0.00282   0.0       2     
saving statistics        0.00222   0.0       2     
compute mean             9.081E-04 0.0       2     
======================== ========= ========= ======