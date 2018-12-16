test for POE_TOO_BIG
====================

============== ===================
checksum32     963,025,495        
date           2018-12-13T12:57:12
engine_version 3.3.0-git68d7d11268
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
0      f1        C    0     4     2,308        11        168        37        37        9,232 
1      p1        P    0     1     156          0.38979   1.121E-05  1.00000   1         15    
1      p2        P    1     2     156          0.34699   3.815E-06  1.00000   1         15    
1      p3        P    2     3     156          0.34487   2.623E-06  1.00000   1         15    
1      p4        P    3     4     156          0.33597   2.384E-06  1.00000   1         15    
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
C    11        1     
P    1.41763   4     
==== ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
read_source_models 0.05618 0.07191 0.00533 0.10703 2      
split_filter       4.56857 NaN     4.56857 4.56857 1      
classical          0.37836 0.23837 0.00769 1.41814 34     
build_hazard_stats 0.00528 NaN     0.00528 0.00528 1      
================== ======= ======= ======= ======= =======

Fastest task
------------
taskno=34, weight=8, duration=0 s, sources="p1 p2 p3 p4"

======== ======= ====== === === =
variable mean    stddev min max n
======== ======= ====== === === =
nsites   1.00000 0.0    1   1   4
weight   15      0.0    15  15  4
======== ======= ====== === === =

Slowest task
------------
taskno=34, weight=62, duration=1 s, sources="p1 p2 p3 p4"

======== ======= ====== === === =
variable mean    stddev min max n
======== ======= ====== === === =
nsites   1.00000 0.0    1   1   4
weight   15      0.0    15  15  4
======== ======= ====== === === =

Data transfer
-------------
================== ============================================================= =========
task               sent                                                          received 
read_source_models converter=776 B fnames=230 B                                  6.1 KB   
split_filter       srcs=4.81 KB srcfilter=380 B seed=14 B                        1.61 MB  
classical          group=1.64 MB param=75.27 KB src_filter=31.21 KB gsims=9.4 KB 154.65 KB
build_hazard_stats pgetter=5.3 KB hstats=67 B                                    1.92 KB  
================== ============================================================= =========

Slowest operations
------------------
======================== ========= ========= ======
operation                time_sec  memory_mb counts
======================== ========= ========= ======
total classical          12        0.39062   34    
get_poes                 7.62870   0.0       2,932 
make_contexts            4.92704   0.0       2,932 
total split_filter       4.56857   4.21484   1     
iter_ruptures            0.25776   0.0       41    
total read_source_models 0.11236   0.29297   2     
store source_info        0.11221   1.03125   34    
managing sources         0.04742   0.76562   1     
aggregate curves         0.01014   0.0       34    
total build_hazard_stats 0.00528   1.26562   1     
store source model       0.00501   0.0       2     
combine pmaps            0.00477   1.26562   1     
saving probability maps  0.00265   0.0       1     
saving statistics        8.948E-04 0.0       1     
compute mean             3.028E-04 0.0       1     
======================== ========= ========= ======