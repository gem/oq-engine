Classical Hazard QA Test, Case 11
=================================

============== ===================
checksum32     3,151,174,296      
date           2017-11-08T18:07:13
engine_version 2.8.0-gite3d0f56   
============== ===================

num_sites = 1, num_imts = 1

Parameters
----------
=============================== ==================
calculation_mode                'classical'       
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              1.0               
ses_per_logic_tree_path         1                 
truncation_level                0.0               
rupture_mesh_spacing            0.01              
complex_fault_mesh_spacing      0.01              
width_of_mfd_bin                0.001             
area_source_discretization      10.0              
ground_motion_correlation_model None              
random_seed                     1066              
master_seed                     0                 
=============================== ==================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gsim_logic_tree.xml <gsim_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
source                  `source_model.xml <source_model.xml>`_                      
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ====== =============== ================
smlt_path weight gsim_logic_tree num_realizations
========= ====== =============== ================
b1_b2     0.200  trivial(1)      1/1             
b1_b3     0.600  trivial(1)      1/1             
b1_b4     0.200  trivial(1)      1/1             
========= ====== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================ ========= ========== ==========
grp_id gsims            distances siteparams ruptparams
====== ================ ========= ========== ==========
0      SadighEtAl1997() rrup      vs30       mag rake  
1      SadighEtAl1997() rrup      vs30       mag rake  
2      SadighEtAl1997() rrup      vs30       mag rake  
====== ================ ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=3, rlzs=3)
  0,SadighEtAl1997(): [0]
  1,SadighEtAl1997(): [1]
  2,SadighEtAl1997(): [2]>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== =========== ============ ============
source_model     grp_id trt                  num_sources eff_ruptures tot_ruptures
================ ====== ==================== =========== ============ ============
source_model.xml 0      Active Shallow Crust 1           3,500        3,500       
source_model.xml 1      Active Shallow Crust 1           3,000        3,000       
source_model.xml 2      Active Shallow Crust 1           2,500        2,500       
================ ====== ==================== =========== ============ ============

============= =====
#TRT models   3    
#sources      3    
#eff_ruptures 9,000
#tot_ruptures 9,000
#tot_weight   0    
============= =====

Informational data
------------------
=========================== ==========================================================================
count_eff_ruptures.received tot 1.8 KB, max_per_task 616 B                                            
count_eff_ruptures.sent     sources 3.49 KB, srcfilter 2 KB, param 1.76 KB, monitor 984 B, gsims 273 B
hazard.input_weight         900.0                                                                     
hazard.n_imts               1                                                                         
hazard.n_levels             4                                                                         
hazard.n_realizations       3                                                                         
hazard.n_sites              1                                                                         
hazard.n_sources            3                                                                         
hazard.output_weight        12.0                                                                      
hostname                    tstation.gem.lan                                                          
require_epsilons            False                                                                     
=========================== ==========================================================================

Slowest sources
---------------
====== ========= ============ ============ ========= ========= =========
grp_id source_id source_class num_ruptures calc_time num_sites num_split
====== ========= ============ ============ ========= ========= =========
1      1         PointSource  3,000        1.724E-04 1         1        
0      1         PointSource  3,500        1.628E-04 1         1        
2      1         PointSource  2,500        1.233E-04 1         1        
====== ========= ============ ============ ========= ========= =========

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
PointSource  4.585E-04 3     
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ========= ========= ========= ========= =========
operation-duration mean      stddev    min       max       num_tasks
count_eff_ruptures 7.382E-04 1.383E-04 5.863E-04 8.566E-04 3        
================== ========= ========= ========= ========= =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
reading composite source model 0.017     0.0       1     
prefiltering source model      0.015     0.0       1     
managing sources               0.004     0.0       1     
store source_info              0.004     0.0       1     
total count_eff_ruptures       0.002     0.0       3     
aggregate curves               5.722E-05 0.0       3     
reading site collection        4.673E-05 0.0       1     
saving probability maps        2.885E-05 0.0       1     
============================== ========= ========= ======