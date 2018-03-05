test for POE_TOO_BIG
====================

============== ===================
checksum32     583,572,055        
date           2018-03-01T10:45:01
engine_version 2.10.0-git18f5063  
============== ===================

num_sites = 1, num_levels = 200

Parameters
----------
=============================== ============================================================================================================================================
calculation_mode                'disaggregation'                                                                                                                            
number_of_logic_tree_samples    0                                                                                                                                           
maximum_distance                {'Subduction Inslab': 200.0, 'Volcanic': 100.0, 'Subduction Interface': 200.0, 'Stable Shallow Crust': 200.0, 'Active Shallow Crust': 200.0}
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
complex   0.330  simple(0,3,0,0,0) 3/3             
point     0.670  simple(0,3,0,0,0) 3/3             
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

Informational data
------------------
========================== ==================================================================================
count_ruptures.received    tot 6.26 KB, max_per_task 568 B                                                   
count_ruptures.sent        param 36.87 KB, sources 21.4 KB, srcfilter 14.09 KB, monitor 5.48 KB, gsims 4.7 KB
hostname                   tstation.gem.lan                                                                  
========================== ==================================================================================

Slowest sources
---------------
========= ================== ============ ========= ========= =========
source_id source_class       num_ruptures calc_time num_sites num_split
========= ================== ============ ========= ========= =========
f1        ComplexFaultSource 2,308        0.061     26        25       
p1        PointSource        156          4.845E-04 2         1        
p2        PointSource        156          1.245E-04 2         1        
p3        PointSource        156          1.166E-04 2         1        
p4        PointSource        156          1.152E-04 2         1        
========= ================== ============ ========= ========= =========

Computation times by source typology
------------------------------------
================== ========= ======
source_class       calc_time counts
================== ========= ======
ComplexFaultSource 0.061     1     
PointSource        8.407E-04 4     
================== ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
count_ruptures     0.005 0.002  0.003 0.013 17       
================== ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
managing sources               2.492     0.0       1     
reading composite source model 0.325     0.0       1     
total count_ruptures           0.083     3.660     17    
store source_info              0.024     0.0       1     
unpickling count_ruptures      8.650E-04 0.0       17    
aggregate curves               3.824E-04 0.0       17    
reading site collection        7.439E-05 0.0       1     
saving probability maps        3.910E-05 0.0       1     
============================== ========= ========= ======