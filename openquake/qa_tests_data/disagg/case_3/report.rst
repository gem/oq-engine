test for POE_TOO_BIG
====================

============== ===================
checksum32     583,572,055        
date           2018-03-26T15:57:45
engine_version 2.10.0-git543cfb0  
============== ===================

num_sites = 1, num_levels = 200

Parameters
----------
=============================== ============================================================================================================================================
calculation_mode                'disaggregation'                                                                                                                            
number_of_logic_tree_samples    0                                                                                                                                           
maximum_distance                {'Stable Shallow Crust': 200.0, 'Active Shallow Crust': 200.0, 'Subduction Interface': 200.0, 'Subduction Inslab': 200.0, 'Volcanic': 100.0}
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
========= ====== ================= ================
smlt_path weight gsim_logic_tree   num_realizations
========= ====== ================= ================
complex   0.330  simple(0,0,0,0,3) 3/3             
point     0.670  simple(0,0,0,0,3) 3/3             
========= ====== ================= ================

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
========= ================== ============ ========= ========== ========= =========
source_id source_class       num_ruptures calc_time split_time num_sites num_split
========= ================== ============ ========= ========== ========= =========
f1        ComplexFaultSource 2,308        0.153     5.398E-04  37        37       
p1        PointSource        156          3.562E-04 3.338E-06  1         1        
p2        PointSource        156          2.556E-04 1.669E-06  1         1        
p3        PointSource        156          2.525E-04 1.431E-06  1         1        
p4        PointSource        156          2.306E-04 1.431E-06  1         1        
========= ================== ============ ========= ========== ========= =========

Computation times by source typology
------------------------------------
================== ========= ======
source_class       calc_time counts
================== ========= ======
ComplexFaultSource 0.153     1     
PointSource        0.001     4     
================== ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
count_ruptures     0.006 0.002  0.002 0.010 34       
================== ===== ====== ===== ===== =========

Informational data
------------------
============== ================================================================================ ========
task           sent                                                                             received
count_ruptures param=73.74 KB sources=38.58 KB srcfilter=28.19 KB monitor=10.96 KB gsims=9.4 KB 12.32 KB
============== ================================================================================ ========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total count_ruptures           0.215     3.629     34    
reading composite source model 0.213     0.0       1     
managing sources               0.051     0.0       1     
store source_info              0.005     0.0       1     
unpickling count_ruptures      0.002     0.0       34    
splitting sources              9.611E-04 0.0       1     
aggregate curves               7.315E-04 0.0       34    
reading site collection        3.226E-04 0.0       1     
saving probability maps        3.052E-05 0.0       1     
============================== ========= ========= ======