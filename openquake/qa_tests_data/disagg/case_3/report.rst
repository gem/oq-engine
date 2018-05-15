test for POE_TOO_BIG
====================

============== ===================
checksum32     583,572,055        
date           2018-05-15T04:14:26
engine_version 3.1.0-git0acbc11   
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

============= ======
#TRT models   2     
#eff_ruptures 2,932 
#tot_ruptures 2,932 
#tot_weight   27,883
============= ======

Slowest sources
---------------
========= ================== ============ ========= ========== ========= ========= ======
source_id source_class       num_ruptures calc_time split_time num_sites num_split events
========= ================== ============ ========= ========== ========= ========= ======
f1        ComplexFaultSource 2,308        0.00186   5.410E-04  37        37        0     
p1        PointSource        156          4.506E-05 1.025E-05  1         1         0     
p2        PointSource        156          3.386E-05 1.907E-06  1         1         0     
p3        PointSource        156          2.909E-05 1.192E-06  1         1         0     
p4        PointSource        156          2.360E-05 1.431E-06  1         1         0     
========= ================== ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
================== ========= ======
source_class       calc_time counts
================== ========= ======
ComplexFaultSource 0.00186   1     
PointSource        1.316E-04 4     
================== ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ========= ========= ======= =========
operation-duration mean    stddev    min       max     num_tasks
prefilter          0.00586 0.00293   0.00175   0.01205 41       
count_ruptures     0.00158 4.402E-04 8.414E-04 0.00283 34       
================== ======= ========= ========= ======= =========

Fastest task
------------
taskno=26, weight=276, duration=0 s, sources="f1"

======== ======= ====== === === =
variable mean    stddev min max n
======== ======= ====== === === =
nsites   1.00000 NaN    1   1   1
weight   276     NaN    276 276 1
======== ======= ====== === === =

Slowest task
------------
taskno=34, weight=187, duration=0 s, sources="p1 p2 p3 p4"

======== ======= ====== === === =
variable mean    stddev min max n
======== ======= ====== === === =
nsites   1.00000 0.0    1   1   4
weight   46      0.0    46  46  4
======== ======= ====== === === =

Informational data
------------------
============== ================================================================================ ========
task           sent                                                                             received
prefilter      srcs=43.9 KB srcfilter=14.25 KB monitor=13.05 KB                                 48.41 KB
count_ruptures param=73.54 KB sources=44.79 KB srcfilter=28.02 KB monitor=11.06 KB gsims=9.4 KB 12.12 KB
============== ================================================================================ ========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total prefilter                0.24009   4.44922   41    
managing sources               0.19493   0.0       1     
reading composite source model 0.14636   0.0       1     
total count_ruptures           0.05377   0.00391   34    
store source_info              0.00578   0.0       1     
unpickling prefilter           0.00385   0.0       41    
unpickling count_ruptures      0.00175   0.0       34    
splitting sources              0.00124   0.0       1     
aggregate curves               7.539E-04 0.0       34    
reading site collection        2.956E-04 0.0       1     
saving probability maps        3.433E-05 0.0       1     
============================== ========= ========= ======