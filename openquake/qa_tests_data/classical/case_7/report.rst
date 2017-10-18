Classical Hazard QA Test, Case 7
================================

============== ===================
checksum32     2,143,775,915      
date           2017-10-18T18:23:00
engine_version 2.7.0-git16fce00   
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
width_of_mfd_bin                1.0               
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
source                  `source_model_1.xml <source_model_1.xml>`_                  
source                  `source_model_2.xml <source_model_2.xml>`_                  
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ====== ========================================== =============== ================
smlt_path weight source_model_file                          gsim_logic_tree num_realizations
========= ====== ========================================== =============== ================
b1        0.700  `source_model_1.xml <source_model_1.xml>`_ trivial(1)      1/1             
b2        0.300  `source_model_2.xml <source_model_2.xml>`_ trivial(1)      1/1             
========= ====== ========================================== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================ ========= ========== ==========
grp_id gsims            distances siteparams ruptparams
====== ================ ========= ========== ==========
0      SadighEtAl1997() rrup      vs30       mag rake  
1      SadighEtAl1997() rrup      vs30       mag rake  
====== ================ ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=2, rlzs=2)
  0,SadighEtAl1997(): [0]
  1,SadighEtAl1997(): [1]>

Number of ruptures per tectonic region type
-------------------------------------------
================== ====== ==================== =========== ============ ============
source_model       grp_id trt                  num_sources eff_ruptures tot_ruptures
================== ====== ==================== =========== ============ ============
source_model_1.xml 0      Active Shallow Crust 2           140          140         
source_model_2.xml 1      Active Shallow Crust 1           91           91          
================== ====== ==================== =========== ============ ============

============= ===
#TRT models   2  
#sources      3  
#eff_ruptures 231
#tot_ruptures 231
#tot_weight   0  
============= ===

Informational data
------------------
=========================== ==========================================================================
count_eff_ruptures.received tot 1.77 KB, max_per_task 605 B                                           
count_eff_ruptures.sent     sources 3.22 KB, srcfilter 2 KB, param 1.77 KB, monitor 978 B, gsims 273 B
hazard.input_weight         378.0                                                                     
hazard.n_imts               1                                                                         
hazard.n_levels             3                                                                         
hazard.n_realizations       2                                                                         
hazard.n_sites              1                                                                         
hazard.n_sources            3                                                                         
hazard.output_weight        3.0                                                                       
hostname                    tstation.gem.lan                                                          
require_epsilons            False                                                                     
=========================== ==========================================================================

Slowest sources
---------------
====== ========= ================== ============ ========= ========= =========
grp_id source_id source_class       num_ruptures calc_time num_sites num_split
====== ========= ================== ============ ========= ========= =========
0      1         SimpleFaultSource  91           0.003     1         1        
1      1         SimpleFaultSource  91           0.002     1         1        
0      2         ComplexFaultSource 49           0.001     1         1        
====== ========= ================== ============ ========= ========= =========

Computation times by source typology
------------------------------------
================== ========= ======
source_class       calc_time counts
================== ========= ======
ComplexFaultSource 0.001     1     
SimpleFaultSource  0.005     2     
================== ========= ======

Duplicated sources
------------------
========= ========= =============
source_id calc_time src_group_ids
========= ========= =============
1         0.005     0 1          
========= ========= =============
Total calc_time in duplicated sources: 0/0 (79%)

Information about the tasks
---------------------------
================== ===== ========= ===== ===== =========
operation-duration mean  stddev    min   max   num_tasks
count_eff_ruptures 0.003 9.128E-04 0.002 0.003 3        
================== ===== ========= ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
reading composite source model 0.121     0.0       1     
total count_eff_ruptures       0.008     0.0       3     
prefiltering source model      0.004     0.0       1     
store source_info              0.004     0.0       1     
managing sources               0.003     0.0       1     
aggregate curves               6.366E-05 0.0       3     
reading site collection        4.554E-05 0.0       1     
saving probability maps        3.004E-05 0.0       1     
============================== ========= ========= ======