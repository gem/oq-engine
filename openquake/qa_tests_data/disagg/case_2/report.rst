QA test for disaggregation case_2
=================================

============== ===================
checksum32     2,473,169,806      
date           2019-06-21T09:42:08
engine_version 3.6.0-git17fd0581aa
============== ===================

num_sites = 2, num_levels = 1, num_rlzs = 4

Parameters
----------
=============================== =================
calculation_mode                'disaggregation' 
number_of_logic_tree_samples    0                
maximum_distance                {'default': 80.0}
investigation_time              1.0              
ses_per_logic_tree_path         1                
truncation_level                3.0              
rupture_mesh_spacing            4.0              
complex_fault_mesh_spacing      4.0              
width_of_mfd_bin                0.1              
area_source_discretization      10.0             
ground_motion_correlation_model None             
minimum_intensity               {}               
random_seed                     23               
master_seed                     0                
ses_seed                        42               
=============================== =================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
============== ======= =============== ================
smlt_path      weight  gsim_logic_tree num_realizations
============== ======= =============== ================
source_model_1 0.50000 simple(2,1)     2               
source_model_2 0.50000 simple(2,0)     2               
============== ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ========================================= =========== ======================= =================
grp_id gsims                                     distances   siteparams              ruptparams       
====== ========================================= =========== ======================= =================
0      '[YoungsEtAl1997SSlab]'                   rrup        vs30                    hypo_depth mag   
1      '[BooreAtkinson2008]' '[ChiouYoungs2008]' rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
2      '[BooreAtkinson2008]' '[ChiouYoungs2008]' rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
====== ========================================= =========== ======================= =================

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=5, rlzs=4)
  0,'[YoungsEtAl1997SSlab]': [0 1]
  1,'[BooreAtkinson2008]': [0]
  1,'[ChiouYoungs2008]': [1]
  2,'[BooreAtkinson2008]': [2]
  2,'[ChiouYoungs2008]': [3]>

Number of ruptures per tectonic region type
-------------------------------------------
================== ====== ==================== ============ ============
source_model       grp_id trt                  eff_ruptures tot_ruptures
================== ====== ==================== ============ ============
source_model_1.xml 0      Subduction Intraslab 1,620        1,815       
source_model_1.xml 1      Active Shallow Crust 3,630        3,630       
source_model_2.xml 2      Active Shallow Crust 1,420        1,420       
================== ====== ==================== ============ ============

============= =====
#TRT models   3    
#eff_ruptures 6,670
#tot_ruptures 6,865
#tot_weight   6,865
============= =====

Slowest sources
---------------
====== ========= ==== ===== ===== ============ ========= ========= ======
grp_id source_id code gidx1 gidx2 num_ruptures calc_time num_sites weight
====== ========= ==== ===== ===== ============ ========= ========= ======
2      1         S    12    14    1,420        5.38621   1.00000   1,420 
1      3         A    8     12    1,815        4.01286   1.00000   1,815 
1      1         A    4     8     1,815        3.93382   1.00000   1,815 
0      2         A    0     4     1,815        2.00751   1.00000   1,815 
====== ========= ==== ===== ===== ============ ========= ========= ======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
A    9.95420   3     
S    5.38621   1     
==== ========= ======

Information about the tasks
---------------------------
====================== ======= ========= ========= ======= =======
operation-duration     mean    stddev    min       max     outputs
build_hazard_stats     0.01086 7.290E-04 0.01035   0.01138 2      
classical              1.49043 0.56780   0.78958   2.57370 8      
classical_split_filter 0.30439 0.45335   1.597E-04 1.05339 12     
read_source_models     0.02666 0.02687   0.00766   0.04566 2      
====================== ======= ========= ========= ======= =======

Fastest task
------------
taskno=0, weight=1815, duration=0 s, sources="1"

======== ======= ====== ===== ===== =
variable mean    stddev min   max   n
======== ======= ====== ===== ===== =
nsites   1.00000 NaN    1     1     1
weight   1,815   NaN    1,815 1,815 1
======== ======= ====== ===== ===== =

Slowest task
------------
taskno=2, weight=1815, duration=1 s, sources="1"

======== ======= ====== ===== ===== =
variable mean    stddev min   max   n
======== ======= ====== ===== ===== =
nsites   1.00000 NaN    1     1     1
weight   1,815   NaN    1,815 1,815 1
======== ======= ====== ===== ===== =

Data transfer
-------------
====================== ============================================================ =========
task                   sent                                                         received 
build_hazard_stats     pgetter=826 B hstats=130 B N=28 B individual_curves=26 B     1.47 KB  
classical              srcs=76.69 KB params=5.45 KB gsims=2.85 KB srcfilter=2.58 KB 1.46 MB  
classical_split_filter srcs=76.69 KB params=5.45 KB gsims=2.85 KB srcfilter=2.58 KB 491.58 KB
read_source_models     converter=626 B fnames=210 B                                 5.41 KB  
====================== ============================================================ =========

Slowest operations
------------------
============================ ========= ========= ======
operation                    time_sec  memory_mb counts
============================ ========= ========= ======
total classical              11        0.25781   8     
make_contexts                5.28918   0.0       6,865 
total classical_split_filter 3.65265   0.0       12    
get_poes                     2.89342   0.0       6,670 
filtering/splitting sources  0.11211   0.0       4     
total read_source_models     0.05333   0.0       2     
aggregate curves             0.04082   0.25781   12    
total build_hazard_stats     0.02172   0.77344   2     
read PoEs                    0.01945   0.77344   2     
saving probability maps      0.00822   0.0       1     
store source model           0.00617   0.0       2     
saving statistics            0.00398   0.0       2     
managing sources             0.00386   0.0       1     
store source_info            0.00171   0.0       1     
compute stats                7.088E-04 0.0       2     
combine pmaps                3.729E-04 0.0       2     
============================ ========= ========= ======