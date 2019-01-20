disaggregation with a complex logic tree
========================================

============== ===================
checksum32     1,766,748,636      
date           2019-01-20T07:36:55
engine_version 3.4.0-git452d0c6835
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
0      1         S    0     2     543          2.51914   0.00273    30        15        767    
1      2         S    2     4     4            0.01561   1.240E-05  2.00000   1         5.65685
2      1         S    4     6     543          2.39760   0.00310    30        15        767    
3      2         X    6     402   1            0.02612   5.245E-06  2.00000   1         1.41421
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= =======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
S    4.93235   3     
X    0.02612   1     
==== ========= ======

Duplicated sources
------------------
['1']
Found 2 source(s) with the same ID and 1 true duplicate(s)
Here is a fake duplicate: 2

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
read_source_models 0.00765 0.00331 0.00532 0.00999 2      
split_filter       0.04237 NaN     0.04237 0.04237 1      
classical          0.23684 0.05925 0.04227 0.33375 21     
build_hazard_stats 0.01195 0.00317 0.00971 0.01419 2      
================== ======= ======= ======= ======= =======

Fastest task
------------
taskno=21, weight=7, duration=0 s, sources="2"

======== ======= ======= ======= ======= =
variable mean    stddev  min     max     n
======== ======= ======= ======= ======= =
nsites   2.00000 0.0     2       2       2
weight   3.53553 3.00000 1.41421 5.65685 2
======== ======= ======= ======= ======= =

Slowest task
------------
taskno=21, weight=94, duration=0 s, sources="2"

======== ======= ======= ======= ======= =
variable mean    stddev  min     max     n
======== ======= ======= ======= ======= =
nsites   2.00000 0.0     2       2       2
weight   3.53553 3.00000 1.41421 5.65685 2
======== ======= ======= ======= ======= =

Data transfer
-------------
================== =============================================================== ========
task               sent                                                            received
read_source_models converter=776 B fnames=220 B                                    13.79 KB
split_filter       srcs=12.16 KB srcfilter=253 B seed=14 B                         18.23 KB
classical          group=37.11 KB param=27.44 KB src_filter=18.44 KB gsims=4.51 KB 83.81 KB
build_hazard_stats pgetter=10.2 KB hstats=402 B individual_curves=26 B             5.89 KB 
================== =============================================================== ========

Slowest operations
------------------
======================== ========= ========= ======
operation                time_sec  memory_mb counts
======================== ========= ========= ======
total classical          4.97370   0.67969   21    
make_contexts            3.09149   0.0       1,091 
get_poes                 1.49680   0.0       1,091 
store source_info        0.04624   0.0       21    
total split_filter       0.04237   1.50391   1     
total build_hazard_stats 0.02390   1.48047   2     
combine pmaps            0.01558   1.41406   2     
total read_source_models 0.01531   0.28125   2     
managing sources         0.00675   0.0       1     
store source model       0.00644   0.0       2     
aggregate curves         0.00484   0.0       21    
saving statistics        0.00461   0.0       2     
saving probability maps  0.00431   0.0       1     
compute quantile-0.85    0.00351   0.0       2     
compute quantile-0.15    0.00325   0.0       2     
compute mean             9.325E-04 0.06641   2     
======================== ========= ========= ======