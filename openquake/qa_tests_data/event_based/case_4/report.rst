Event-Based Hazard QA Test, Case 4
==================================

============== ===================
checksum32     2,872,781,101      
date           2018-01-11T04:30:36
engine_version 2.9.0-git3c583c4   
============== ===================

num_sites = 1, num_imts = 1

Parameters
----------
=============================== ==================
calculation_mode                'event_based'     
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              1.0               
ses_per_logic_tree_path         50                
truncation_level                0.0               
rupture_mesh_spacing            1.0               
complex_fault_mesh_spacing      1.0               
width_of_mfd_bin                1.0               
area_source_discretization      10.0              
ground_motion_correlation_model None              
random_seed                     42                
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
b1        1.000  trivial(1)      1/1             
========= ====== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================ ========= ========== ==========
grp_id gsims            distances siteparams ruptparams
====== ================ ========= ========== ==========
0      SadighEtAl1997() rrup      vs30       mag rake  
====== ================ ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)
  0,SadighEtAl1997(): [0]>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== ============ ============
source_model     grp_id trt                  eff_ruptures tot_ruptures
================ ====== ==================== ============ ============
source_model.xml 0      Active Shallow Crust 10           10          
================ ====== ==================== ============ ============

Informational data
------------------
========================= =========================================================================
compute_ruptures.received max_per_task 9.36 KB, tot 9.36 KB                                        
compute_ruptures.sent     sources 1.26 KB, src_filter 722 B, param 582 B, monitor 323 B, gsims 91 B
hazard.input_weight       10.0                                                                     
hazard.n_imts             1                                                                        
hazard.n_levels           3                                                                        
hazard.n_realizations     1                                                                        
hazard.n_sites            1                                                                        
hazard.n_sources          1                                                                        
hazard.output_weight      0.5                                                                      
hostname                  tstation.gem.lan                                                         
require_epsilons          False                                                                    
========================= =========================================================================

Slowest sources
---------------
========= ================= ============ ========= ========= =========
source_id source_class      num_ruptures calc_time num_sites num_split
========= ================= ============ ========= ========= =========
1         SimpleFaultSource 10           0.0       1         0        
========= ================= ============ ========= ========= =========

Computation times by source typology
------------------------------------
================= ========= ======
source_class      calc_time counts
================= ========= ======
SimpleFaultSource 0.0       1     
================= ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
compute_ruptures   0.031 NaN    0.031 0.031 1        
================== ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
managing sources               0.046     0.0       1     
total compute_ruptures         0.031     0.0       1     
making contexts                0.018     0.0       10    
reading composite source model 0.005     0.0       1     
store source_info              0.003     0.0       1     
saving ruptures                0.003     0.0       1     
setting event years            0.001     0.0       1     
reading site collection        4.768E-05 0.0       1     
============================== ========= ========= ======