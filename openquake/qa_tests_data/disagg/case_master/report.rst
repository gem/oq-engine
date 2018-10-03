disaggregation with a complex logic tree
========================================

============== ===================
checksum32     1,766,748,636      
date           2018-10-03T15:00:46
engine_version 3.3.0-gitd9f5dca908
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
source                  `source_model_1.xml <source_model_1.xml>`_                  
source                  `source_model_2.xml <source_model_2.xml>`_                  
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
0      1         S    0     2     543          5.21928   0.00476    30        15        767    
1      2         S    2     4     4            0.01498   1.693E-05  2.00000   1         5.65685
2      1         S    0     2     543          4.76302   0.00376    30        15        767    
3      2         X    2     398   1            0.07710   5.245E-06  2.00000   1         1.41421
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= =======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
S    9.99729   3     
X    0.07710   1     
==== ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ========= ======= ======= =======
operation-duration mean    stddev    min     max     outputs
read_source_models 0.02350 0.01920   0.00992 0.03707 2      
split_filter       0.07300 NaN       0.07300 0.07300 1      
classical          0.67413 0.22417   0.09474 1.02381 15     
build_hazard_stats 0.01674 2.394E-04 0.01657 0.01691 2      
================== ======= ========= ======= ======= =======

Fastest task
------------
taskno=15, weight=7, duration=0 s, sources="2"

======== ======= ======= ======= ======= =
variable mean    stddev  min     max     n
======== ======= ======= ======= ======= =
nsites   2.00000 0.0     2       2       2
weight   3.53553 3.00000 1.41421 5.65685 2
======== ======= ======= ======= ======= =

Slowest task
------------
taskno=6, weight=135, duration=1 s, sources="1"

======== ======= ======= === === =
variable mean    stddev  min max n
======== ======= ======= === === =
nsites   2.00000 0.0     2   2   3
weight   45      5.65685 39  50  3
======== ======= ======= === === =

Data transfer
-------------
================== ============================================================================== ========
task               sent                                                                           received
read_source_models monitor=736 B converter=638 B fnames=370 B                                     13.83 KB
split_filter       srcs=12.14 KB monitor=381 B srcfilter=253 B sample_factor=21 B seed=14 B       18.11 KB
classical          group=31.01 KB param=20.21 KB monitor=5.05 KB src_filter=3.22 KB gsims=3.22 KB 60.67 KB
build_hazard_stats pgetter=9.28 KB monitor=708 B hstats=402 B                                     5.89 KB 
================== ============================================================================== ========

Slowest operations
------------------
======================== ======== ========= ======
operation                time_sec memory_mb counts
======================== ======== ========= ======
total classical          10       0.60938   15    
make_contexts            6.37975  0.0       1,091 
get_poes                 2.96191  0.0       1,091 
iter_ruptures            0.68491  0.0       32    
updating source_info     0.08168  0.0       1     
store source_info        0.08025  0.0       15    
total split_filter       0.07300  0.0       1     
total read_source_models 0.04699  0.07812   2     
total build_hazard_stats 0.03348  0.58203   2     
managing sources         0.02614  0.0       1     
saving probability maps  0.02305  0.0       1     
combine pmaps            0.01946  0.58203   2     
compute quantile-0.85    0.00607  0.0       2     
compute quantile-0.15    0.00605  0.0       2     
aggregate curves         0.00436  0.0       15    
saving statistics        0.00355  0.0       2     
compute mean             0.00125  0.0       2     
======================== ======== ========= ======