disaggregation with a complex logic tree
========================================

============== ===================
checksum32     1,766,748,636      
date           2019-03-14T01:45:15
engine_version 3.4.0-gita06742ffe6
============== ===================

num_sites = 2, num_levels = 102, num_rlzs = 8

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
b1        0.25000 complex(2,2)    4               
b2        0.75000 complex(2,2)    4               
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ========================================= =========== ======================= =================
grp_id gsims                                     distances   siteparams              ruptparams       
====== ========================================= =========== ======================= =================
0      '[BooreAtkinson2008]' '[ChiouYoungs2008]' rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
1      '[AkkarBommer2010]' '[ChiouYoungs2008]'   rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
2      '[BooreAtkinson2008]' '[ChiouYoungs2008]' rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
3      '[AkkarBommer2010]' '[ChiouYoungs2008]'   rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
====== ========================================= =========== ======================= =================

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=8, rlzs=8)
  0,'[BooreAtkinson2008]': [0 1]
  0,'[ChiouYoungs2008]': [2 3]
  1,'[AkkarBommer2010]': [0 2]
  1,'[ChiouYoungs2008]': [1 3]
  2,'[BooreAtkinson2008]': [4 5]
  2,'[ChiouYoungs2008]': [6 7]
  3,'[AkkarBommer2010]': [4 6]
  3,'[ChiouYoungs2008]': [5 7]>

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
0      1         S    0     2     543          2.04930   0.00318    30        15        767    
2      1         S    4     6     543          2.03717   0.00197    30        15        767    
3      2         X    6     402   1            0.02708   4.053E-06  2.00000   1         1.41421
1      2         S    2     4     4            0.00992   1.836E-05  2.00000   1         5.65685
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= =======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
S    4.09640   3     
X    0.02708   1     
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
read_source_models 0.01384 0.00555 0.00992 0.01777 2      
split_filter       0.02400 0.02834 0.00396 0.04404 2      
classical          0.19849 0.06213 0.03880 0.33867 21     
build_hazard_stats 0.01317 0.00557 0.00922 0.01711 2      
================== ======= ======= ======= ======= =======

Fastest task
------------
taskno=20, weight=7, duration=0 s, sources="1"

======== ======= ======= ======= ======= =
variable mean    stddev  min     max     n
======== ======= ======= ======= ======= =
nsites   2.00000 0.0     2       2       2
weight   3.53553 3.00000 1.41421 5.65685 2
======== ======= ======= ======= ======= =

Slowest task
------------
taskno=8, weight=94, duration=0 s, sources="1"

======== ======= ======= === === =
variable mean    stddev  min max n
======== ======= ======= === === =
nsites   2.00000 0.0     2   2   3
weight   31      7.25718 25  39  3
======== ======= ======= === === =

Data transfer
-------------
================== ============================================================== =========
task               sent                                                           received 
read_source_models converter=626 B fnames=220 B                                   13.92 KB 
split_filter       srcs=12.82 KB srcfilter=506 B dummy=28 B                       18.84 KB 
classical          group=37.52 KB param=27.44 KB gsims=5.57 KB src_filter=4.51 KB 434.34 KB
build_hazard_stats pgetter=10.18 KB hstats=390 B N=28 B individual_curves=26 B    5.96 KB  
================== ============================================================== =========

Slowest operations
------------------
======================== ======== ========= ======
operation                time_sec memory_mb counts
======================== ======== ========= ======
total classical          4.16834  2.00391   21    
make_contexts            1.80321  0.0       1,091 
get_poes                 0.92900  0.0       1,091 
total split_filter       0.04800  2.20703   2     
aggregate curves         0.03525  0.0       21    
total read_source_models 0.02769  0.14453   2     
total build_hazard_stats 0.02633  0.48047   2     
combine pmaps            0.01866  0.48047   2     
saving probability maps  0.01215  0.0       1     
managing sources         0.00976  0.0       1     
compute stats            0.00710  0.0       2     
store source model       0.00621  0.0       2     
saving statistics        0.00377  0.0       2     
store source_info        0.00233  0.0       1     
======================== ======== ========= ======