test for POE_TOO_BIG
====================

============== ===================
checksum32     3,490,620,350      
date           2019-01-27T08:28:45
engine_version 3.4.0-git7f110aaa0b
============== ===================

num_sites = 1, num_levels = 200

Parameters
----------
=============================== ============================================================================================================================================
calculation_mode                'disaggregation'                                                                                                                            
number_of_logic_tree_samples    0                                                                                                                                           
maximum_distance                {'Stable Shallow Crust': 200.0, 'Active Shallow Crust': 200.0, 'Volcanic': 100.0, 'Subduction Interface': 200.0, 'Subduction Inslab': 200.0}
investigation_time              50.0                                                                                                                                        
ses_per_logic_tree_path         1                                                                                                                                           
truncation_level                3.0                                                                                                                                         
rupture_mesh_spacing            5.0                                                                                                                                         
complex_fault_mesh_spacing      5.0                                                                                                                                         
width_of_mfd_bin                0.1                                                                                                                                         
area_source_discretization      15.0                                                                                                                                        
ground_motion_correlation_model None                                                                                                                                        
minimum_intensity               {}                                                                                                                                          
random_seed                     23                                                                                                                                          
master_seed                     0                                                                                                                                           
ses_seed                        42                                                                                                                                          
=============================== ============================================================================================================================================

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
========= ======= ================= ================
smlt_path weight  gsim_logic_tree   num_realizations
========= ======= ================= ================
complex   0.33000 simple(3,0,0,0,0) 3/3             
point     0.67000 simple(3,0,0,0,0) 3/3             
========= ======= ================= ================

Required parameters per tectonic region type
--------------------------------------------
====== ==================================================== ============== ========== ==========
grp_id gsims                                                distances      siteparams ruptparams
====== ==================================================== ============== ========== ==========
0      BindiEtAl2011() BindiEtAl2014Rhyp() CauzziEtAl2014() rhypo rjb rrup vs30       mag rake  
1      BindiEtAl2011() BindiEtAl2014Rhyp() CauzziEtAl2014() rhypo rjb rrup vs30       mag rake  
====== ==================================================== ============== ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=6, rlzs=6)
  0,BindiEtAl2011(): [0]
  0,BindiEtAl2014Rhyp(): [1]
  0,CauzziEtAl2014(): [2]
  1,BindiEtAl2011(): [3]
  1,BindiEtAl2014Rhyp(): [4]
  1,CauzziEtAl2014(): [5]>

Number of ruptures per tectonic region type
-------------------------------------------
============================= ====== ==================== ============ ============
source_model                  grp_id trt                  eff_ruptures tot_ruptures
============================= ====== ==================== ============ ============
source_model_test_complex.xml 0      Active Shallow Crust 2,308        2,308       
source_model_test_point.xml   1      Active Shallow Crust 624          624         
============================= ====== ==================== ============ ============

============= =====
#TRT models   2    
#eff_ruptures 2,932
#tot_ruptures 2,932
#tot_weight   9,294
============= =====

Slowest sources
---------------
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======
grp_id source_id code gidx1 gidx2 num_ruptures calc_time split_time num_sites num_split weight
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======
0      f1        C    0     4     2,308        10        163        37        37        9,232 
1      p1        P    4     5     156          0.39963   1.073E-05  1.00000   1         15    
1      p4        P    7     8     156          0.33029   1.907E-06  1.00000   1         15    
1      p2        P    5     6     156          0.32401   2.861E-06  1.00000   1         15    
1      p3        P    6     7     156          0.32364   2.384E-06  1.00000   1         15    
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
C    10        1     
P    1.37757   4     
==== ========= ======

Duplicated sources
------------------
Found 0 source(s) with the same ID and 0 true duplicate(s)

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
read_source_models 0.04076 0.05399 0.00258 0.07893 2      
split_filter       4.41548 NaN     4.41548 4.41548 1      
classical          0.34126 0.22841 0.00817 1.37809 34     
build_hazard_stats 0.00572 NaN     0.00572 0.00572 1      
================== ======= ======= ======= ======= =======

Fastest task
------------
taskno=19, weight=8, duration=0 s, sources="f1"

======== ======= ====== ======= ======= =
variable mean    stddev min     max     n
======== ======= ====== ======= ======= =
nsites   1.00000 NaN    1       1       1
weight   8.00000 NaN    8.00000 8.00000 1
======== ======= ====== ======= ======= =

Slowest task
------------
taskno=33, weight=62, duration=1 s, sources="f1"

======== ======= ====== === === =
variable mean    stddev min max n
======== ======= ====== === === =
nsites   1.00000 0.0    1   1   4
weight   15      0.0    15  15  4
======== ======= ====== === === =

Data transfer
-------------
================== =============================================================== =========
task               sent                                                            received 
read_source_models converter=626 B fnames=230 B                                    6.27 KB  
split_filter       srcs=4.9 KB srcfilter=380 B seed=14 B                           1.62 MB  
classical          group=1.65 MB param=75.27 KB src_filter=31.21 KB gsims=13.58 KB 155.02 KB
build_hazard_stats pgetter=6.09 KB hstats=67 B individual_curves=13 B              11.87 KB 
================== =============================================================== =========

Slowest operations
------------------
======================== ========= ========= ======
operation                time_sec  memory_mb counts
======================== ========= ========= ======
total classical          11        0.98828   34    
get_poes                 6.84276   0.0       2,932 
make_contexts            4.48047   0.0       2,932 
total split_filter       4.41548   6.05078   1     
total read_source_models 0.08151   0.90234   2     
managing sources         0.04593   0.00391   1     
aggregate curves         0.01154   0.0       34    
total build_hazard_stats 0.00572   1.42578   1     
combine pmaps            0.00482   1.42578   1     
store source model       0.00429   0.0       2     
saving statistics        0.00281   0.0       1     
saving probability maps  0.00225   0.0       1     
store source_info        0.00192   0.0       1     
compute mean             5.367E-04 0.0       1     
build individual hmaps   1.366E-04 0.0       1     
======================== ========= ========= ======