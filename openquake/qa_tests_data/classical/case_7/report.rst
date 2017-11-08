Classical Hazard QA Test, Case 7
================================

============== ===================
checksum32     359,954,679        
date           2017-11-08T18:07:14
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
========= ====== =============== ================
smlt_path weight gsim_logic_tree num_realizations
========= ====== =============== ================
b1        0.700  trivial(1)      1/1             
b2        0.300  trivial(1)      1/1             
========= ====== =============== ================

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

Informational data
------------------
====================== ==============================================================================
hazard.input_weight    378.0                                                                         
hazard.n_imts          1                                                                             
hazard.n_levels        3                                                                             
hazard.n_realizations  2                                                                             
hazard.n_sites         1                                                                             
hazard.n_sources       3                                                                             
hazard.output_weight   3.0                                                                           
hostname               tstation.gem.lan                                                              
pmap_from_trt.received tot 2.4 KB, max_per_task 1.21 KB                                              
pmap_from_trt.sent     sources 2.23 KB, src_filter 1.34 KB, param 1.18 KB, monitor 656 B, gsims 182 B
require_epsilons       False                                                                         
====================== ==============================================================================

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
pmap_from_trt      0.828 0.188  0.695 0.962 2        
================== ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total pmap_from_trt            1.657     3.109     2     
making contexts                1.066     0.0       140   
reading composite source model 0.137     0.0       1     
SadighEtAl1997().get_poes      0.018     0.0       140   
store source_info              0.005     0.0       1     
saving probability maps        0.005     0.0       1     
prefiltering source model      0.004     0.0       1     
managing sources               0.002     0.0       1     
aggregate curves               1.218E-04 0.0       2     
reading site collection        4.292E-05 0.0       1     
============================== ========= ========= ======