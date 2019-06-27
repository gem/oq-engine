test for POE_TOO_BIG
====================

============== ===================
checksum32     3,490,620,350      
date           2019-06-24T15:33:30
engine_version 3.6.0-git4b6205639c
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

  <RlzsAssoc(size=18, rlzs=6)>

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
====== ========= ==== ===== ===== ============ ========= ========= ====== =============
grp_id source_id code gidx1 gidx2 num_ruptures calc_time num_sites weight checksum     
====== ========= ==== ===== ===== ============ ========= ========= ====== =============
0      f1        C    0     4     2,308        9.39613   1.00000   2,308  985,636,512  
1      p2        P    5     6     156          0.52078   1.00000   156    2,335,114,969
1      p4        P    7     8     156          0.51332   1.00000   156    1,049,823,183
1      p3        P    6     7     156          0.50690   1.00000   156    2,795,897,910
1      p1        P    4     5     156          0.48139   1.00000   156    4,081,189,696
====== ========= ==== ===== ===== ============ ========= ========= ====== =============

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
C    9.39613   1     
P    2.02239   4     
==== ========= ======

Information about the tasks
---------------------------
====================== ======= ======= ========= ======= =======
operation-duration     mean    stddev  min       max     outputs
build_hazard_stats     0.00413 NaN     0.00413   0.00413 1      
classical              0.68221 1.05962 0.23993   5.23959 21     
classical_split_filter 0.26710 0.96192 1.605E-04 4.89370 26     
read_source_models     0.05917 0.07970 0.00282   0.11553 2      
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
====================== ============================================================= ========
task                   sent                                                          received
build_hazard_stats     pgetter=0 B individual_curves=0 B hstats=0 B N=0 B            11.78 KB
classical              srcs=1.63 MB params=57.92 KB gsims=12.19 KB srcfilter=9.29 KB 703.1 KB
classical_split_filter srcs=1.63 MB params=57.92 KB gsims=12.19 KB srcfilter=9.29 KB 1.86 MB 
read_source_models     converter=626 B fnames=230 B                                  6.29 KB 
====================== ============================================================= ========

Slowest operations
------------------
============================ ========= ========= ======
operation                    time_sec  memory_mb counts
============================ ========= ========= ======
total classical              14        3.79688   21    
get_poes                     9.92137   0.0       2,932 
make_contexts                7.94348   0.0       2,932 
total classical_split_filter 6.94470   3.28906   26    
filtering/splitting sources  4.90516   3.28906   5     
total read_source_models     0.11835   0.0       2     
aggregate curves             0.05556   1.03125   26    
store source model           0.00664   0.0       2     
saving probability maps      0.00461   0.0       1     
total build_hazard_stats     0.00413   0.0       1     
managing sources             0.00397   0.0       1     
read PoEs                    0.00353   0.0       1     
saving statistics            0.00170   0.0       1     
store source_info            0.00148   0.0       1     
compute stats                2.303E-04 0.0       1     
combine pmaps                1.185E-04 0.0       1     
============================ ========= ========= ======