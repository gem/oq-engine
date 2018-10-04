test for POE_TOO_BIG
====================

============== ===================
checksum32     583,572,055        
date           2018-10-03T15:00:53
engine_version 3.3.0-gitd9f5dca908
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
======================= ================================================================
Name                    File                                                            
======================= ================================================================
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                    
job_ini                 `job.ini <job.ini>`_                                            
source                  `source_model_test_complex.xml <source_model_test_complex.xml>`_
source                  `source_model_test_point.xml <source_model_test_point.xml>`_    
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_    
======================= ================================================================

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
0      f1        C    0     4     2,308        40        0.02893    37        37        9,232 
1      p1        P    0     1     156          1.30667   6.199E-06  1.00000   1         15    
1      p2        P    1     2     156          0.74640   2.861E-06  1.00000   1         15    
1      p3        P    2     3     156          0.62523   2.384E-06  1.00000   1         15    
1      p4        P    3     4     156          0.60475   1.907E-06  1.00000   1         15    
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
C    40        1     
P    3.28305   4     
==== ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
read_source_models 0.09603 0.13034 0.00386 0.18819 2      
split_filter       0.06333 NaN     0.06333 0.06333 1      
classical          1.27734 0.56311 0.30700 3.28560 34     
build_hazard_stats 0.00816 NaN     0.00816 0.00816 1      
================== ======= ======= ======= ======= =======

Fastest task
------------
taskno=20, weight=8, duration=0 s, sources="f1"

======== ======= ====== ======= ======= =
variable mean    stddev min     max     n
======== ======= ====== ======= ======= =
nsites   1.00000 NaN    1       1       1
weight   8.00000 NaN    8.00000 8.00000 1
======== ======= ====== ======= ======= =

Slowest task
------------
taskno=34, weight=62, duration=3 s, sources="p1 p2 p3 p4"

======== ======= ====== === === =
variable mean    stddev min max n
======== ======= ====== === === =
nsites   1.00000 0.0    1   1   4
weight   15      0.0    15  15  4
======== ======= ====== === === =

Data transfer
-------------
================== =============================================================================== =========
task               sent                                                                            received 
read_source_models monitor=736 B converter=638 B fnames=380 B                                      6.14 KB  
split_filter       srcs=4.79 KB monitor=381 B srcfilter=380 B sample_factor=21 B seed=14 B         10.79 KB 
classical          param=76.67 KB group=43.06 KB src_filter=11.52 KB monitor=11.46 KB gsims=9.4 KB 154.65 KB
build_hazard_stats pgetter=5.82 KB monitor=354 B hstats=67 B                                       1.92 KB  
================== =============================================================================== =========

Slowest operations
------------------
======================== ========= ========= ======
operation                time_sec  memory_mb counts
======================== ========= ========= ======
total classical          43        0.82031   34    
iter_ruptures            21        0.0       41    
get_poes                 13        0.0       2,932 
make_contexts            8.39619   0.0       2,932 
total read_source_models 0.19205   0.31250   2     
store source_info        0.17140   0.0       34    
updating source_info     0.07133   0.0       1     
managing sources         0.06502   0.0       1     
total split_filter       0.06333   0.0       1     
aggregate curves         0.01040   0.0       34    
total build_hazard_stats 0.00816   0.05078   1     
combine pmaps            0.00739   0.05078   1     
saving probability maps  0.00375   0.0       1     
saving statistics        8.228E-04 0.0       1     
compute mean             4.766E-04 0.0       1     
======================== ========= ========= ======