test for POE_TOO_BIG
====================

============== ===================
checksum32     3,490,620,350      
date           2019-03-19T10:03:35
engine_version 3.5.0-gitad6b69ea66
============== ===================

num_sites = 1, num_levels = 200, num_rlzs = 6

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
complex   0.33000 simple(3,0,0,0,0) 3               
point     0.67000 simple(3,0,0,0,0) 3               
========= ======= ================= ================

Required parameters per tectonic region type
--------------------------------------------
====== ========================================================== ============== ========== ==========
grp_id gsims                                                      distances      siteparams ruptparams
====== ========================================================== ============== ========== ==========
0      '[BindiEtAl2011]' '[BindiEtAl2014Rhyp]' '[CauzziEtAl2014]' rhypo rjb rrup vs30       mag rake  
1      '[BindiEtAl2011]' '[BindiEtAl2014Rhyp]' '[CauzziEtAl2014]' rhypo rjb rrup vs30       mag rake  
====== ========================================================== ============== ========== ==========

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=6, rlzs=6)
  0,'[BindiEtAl2011]': [0]
  0,'[BindiEtAl2014Rhyp]': [1]
  0,'[CauzziEtAl2014]': [2]
  1,'[BindiEtAl2011]': [3]
  1,'[BindiEtAl2014Rhyp]': [4]
  1,'[CauzziEtAl2014]': [5]>

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
0      f1        C    0     4     2,308        8.75671   163        37        37        9,232 
1      p4        P    7     8     156          0.41449   1.669E-06  1.00000   1         15    
1      p1        P    4     5     156          0.41025   1.049E-05  1.00000   1         15    
1      p2        P    5     6     156          0.40459   3.099E-06  1.00000   1         15    
1      p3        P    6     7     156          0.40137   2.146E-06  1.00000   1         15    
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
C    8.75671   1     
P    1.63069   4     
==== ========= ======

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
read_source_models 0.04114 0.05427 0.00277 0.07951 2      
split_filter       4.41828 NaN     4.41828 4.41828 1      
classical          0.34824 0.29895 0.00616 1.78100 30     
build_hazard_stats 0.00703 NaN     0.00703 0.00703 1      
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
taskno=29, weight=130, duration=1 s, sources="f1"

======== ======= ====== ======= === =
variable mean    stddev min     max n
======== ======= ====== ======= === =
nsites   1.00000 0.0    1       1   8
weight   16      13     4.00000 48  8
======== ======= ====== ======= === =

Data transfer
-------------
================== =============================================================== =========
task               sent                                                            received 
read_source_models converter=626 B fnames=230 B                                    6.27 KB  
split_filter       srcs=4.9 KB srcfilter=380 B dummy=14 B                          1.62 MB  
classical          group=1.64 MB param=66.42 KB gsims=14.06 KB src_filter=10.17 KB 908.81 KB
build_hazard_stats pgetter=6.08 KB hstats=65 B N=14 B individual_curves=13 B       11.87 KB 
================== =============================================================== =========

Slowest operations
------------------
======================== ========= ========= ======
operation                time_sec  memory_mb counts
======================== ========= ========= ======
total classical          10        2.29297   30    
total split_filter       4.41828   5.56641   1     
get_poes                 4.35649   0.0       2,932 
make_contexts            2.92153   0.0       2,932 
total read_source_models 0.08228   0.86328   2     
aggregate curves         0.05572   0.96094   30    
managing sources         0.04353   0.00391   1     
saving probability maps  0.01441   0.0       1     
total build_hazard_stats 0.00703   0.67188   1     
combine pmaps            0.00576   0.67188   1     
saving statistics        0.00338   0.0       1     
store source model       0.00324   0.0       2     
store source_info        0.00230   0.0       1     
compute stats            9.141E-04 0.0       1     
======================== ========= ========= ======