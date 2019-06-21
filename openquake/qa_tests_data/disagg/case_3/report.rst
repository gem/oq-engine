test for POE_TOO_BIG
====================

============== ===================
checksum32     3,490,620,350      
date           2019-06-21T09:42:02
engine_version 3.6.0-git17fd0581aa
============== ===================

num_sites = 1, num_levels = 200, num_rlzs = 6

Parameters
----------
=============================== ==============================================================================================================================================================
calculation_mode                'disaggregation'                                                                                                                                              
number_of_logic_tree_samples    0                                                                                                                                                             
maximum_distance                {'default': 200.0, 'Stable Shallow Crust': 200.0, 'Active Shallow Crust': 200.0, 'Volcanic': 100.0, 'Subduction Interface': 200.0, 'Subduction Inslab': 200.0}
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
=============================== ==============================================================================================================================================================

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
#tot_weight   2,932
============= =====

Slowest sources
---------------
====== ========= ==== ===== ===== ============ ========= ========= ======
grp_id source_id code gidx1 gidx2 num_ruptures calc_time num_sites weight
====== ========= ==== ===== ===== ============ ========= ========= ======
0      f1        C    0     4     2,308        9.51144   1.00000   2,308 
1      p3        P    6     7     156          0.50030   1.00000   156   
1      p4        P    7     8     156          0.49599   1.00000   156   
1      p2        P    5     6     156          0.49455   1.00000   156   
1      p1        P    4     5     156          0.49149   1.00000   156   
====== ========= ==== ===== ===== ============ ========= ========= ======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
C    9.51144   1     
P    1.98233   4     
==== ========= ======

Information about the tasks
---------------------------
====================== ======= ======= ========= ======= =======
operation-duration     mean    stddev  min       max     outputs
build_hazard_stats     0.00416 NaN     0.00416   0.00416 1      
classical              0.68208 1.02839 0.27617   5.10898 21     
classical_split_filter 0.26053 0.93672 1.585E-04 4.76503 26     
read_source_models     0.04967 0.06589 0.00308   0.09626 2      
====================== ======= ======= ========= ======= =======

Fastest task
------------
taskno=0, weight=2308, duration=0 s, sources="p4"

======== ======= ====== ===== ===== =
variable mean    stddev min   max   n
======== ======= ====== ===== ===== =
nsites   1.00000 NaN    1     1     1
weight   2,308   NaN    2,308 2,308 1
======== ======= ====== ===== ===== =

Slowest task
------------
taskno=0, weight=2308, duration=4 s, sources="p4"

======== ======= ====== ===== ===== =
variable mean    stddev min   max   n
======== ======= ====== ===== ===== =
nsites   1.00000 NaN    1     1     1
weight   2,308   NaN    2,308 2,308 1
======== ======= ====== ===== ===== =

Data transfer
-------------
====================== ============================================================= =========
task                   sent                                                          received 
build_hazard_stats     pgetter=0 B individual_curves=0 B hstats=0 B N=0 B            11.78 KB 
classical              srcs=1.63 MB params=57.92 KB gsims=12.19 KB srcfilter=9.29 KB 702.49 KB
classical_split_filter srcs=1.63 MB params=57.92 KB gsims=12.19 KB srcfilter=9.29 KB 1.86 MB  
read_source_models     converter=626 B fnames=230 B                                  6.27 KB  
====================== ============================================================= =========

Slowest operations
------------------
============================ ========= ========= ======
operation                    time_sec  memory_mb counts
============================ ========= ========= ======
total classical              14        2.79688   21    
get_poes                     9.78435   0.0       2,932 
make_contexts                7.86455   0.0       2,932 
total classical_split_filter 6.77385   2.54297   26    
filtering/splitting sources  4.77484   2.54297   5     
total read_source_models     0.09934   0.25781   2     
aggregate curves             0.05131   1.03125   26    
managing sources             0.00478   0.0       1     
saving probability maps      0.00454   0.0       1     
store source model           0.00449   0.0       2     
total build_hazard_stats     0.00416   0.0       1     
read PoEs                    0.00357   0.0       1     
saving statistics            0.00165   0.0       1     
store source_info            0.00151   0.0       1     
compute stats                2.265E-04 0.0       1     
combine pmaps                1.135E-04 0.0       1     
============================ ========= ========= ======