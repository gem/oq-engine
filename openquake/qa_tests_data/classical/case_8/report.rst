Classical Hazard QA Test, Case 8
================================

============== ===================
checksum32     745,347,419        
date           2017-11-08T18:07:11
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
rupture_mesh_spacing            0.1               
complex_fault_mesh_spacing      0.1               
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
b1_b2     0.300  trivial(1)      1/1             
b1_b3     0.300  trivial(1)      1/1             
b1_b4     0.400  trivial(1)      1/1             
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
source_model.xml 0      Active Shallow Crust 1           3,000        3,000       
source_model.xml 1      Active Shallow Crust 1           3,000        3,000       
source_model.xml 2      Active Shallow Crust 1           3,000        3,000       
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
hazard.output_weight        4.0                                                                       
hostname                    tstation.gem.lan                                                          
require_epsilons            False                                                                     
=========================== ==========================================================================

Slowest sources
---------------
====== ========= ============ ============ ========= ========= =========
grp_id source_id source_class num_ruptures calc_time num_sites num_split
====== ========= ============ ============ ========= ========= =========
1      1         PointSource  3,000        1.929E-04 1         1        
0      1         PointSource  3,000        1.740E-04 1         1        
2      1         PointSource  3,000        1.523E-04 1         1        
====== ========= ============ ============ ========= ========= =========

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
PointSource  5.193E-04 3     
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ========= ========= ========= ========= =========
operation-duration mean      stddev    min       max       num_tasks
count_eff_ruptures 8.372E-04 1.071E-04 7.391E-04 9.515E-04 3        
================== ========= ========= ========= ========= =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
reading composite source model 0.016     0.0       1     
prefiltering source model      0.014     0.0       1     
managing sources               0.004     0.0       1     
store source_info              0.004     0.0       1     
total count_eff_ruptures       0.003     0.0       3     
aggregate curves               5.817E-05 0.0       3     
reading site collection        4.578E-05 0.0       1     
saving probability maps        2.956E-05 0.0       1     
============================== ========= ========= ======