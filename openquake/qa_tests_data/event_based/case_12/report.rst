Event Based QA Test, Case 12
============================

============== ===================
checksum32     2,564,275,427      
date           2018-01-11T04:31:21
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
ses_per_logic_tree_path         3500              
truncation_level                2.0               
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
b1        1.000  trivial(1,1)    1/1             
========= ====== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== =================== ========= ========== ==========
grp_id gsims               distances siteparams ruptparams
====== =================== ========= ========== ==========
0      SadighEtAl1997()    rrup      vs30       mag rake  
1      BooreAtkinson2008() rjb       vs30       mag rake  
====== =================== ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=2, rlzs=1)
  0,SadighEtAl1997(): [0]
  1,BooreAtkinson2008(): [0]>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== ============ ============
source_model     grp_id trt                  eff_ruptures tot_ruptures
================ ====== ==================== ============ ============
source_model.xml 0      Active Shallow Crust 1            1           
source_model.xml 1      Stable Continental   1            1           
================ ====== ==================== ============ ============

============= =
#TRT models   2
#eff_ruptures 2
#tot_ruptures 2
#tot_weight   0
============= =

Informational data
------------------
========================= ==============================================================================
compute_ruptures.received tot 127.06 KB, max_per_task 65.03 KB                                          
compute_ruptures.sent     sources 2.63 KB, src_filter 1.41 KB, param 1.14 KB, monitor 646 B, gsims 193 B
hazard.input_weight       0.2                                                                           
hazard.n_imts             1                                                                             
hazard.n_levels           3                                                                             
hazard.n_realizations     1                                                                             
hazard.n_sites            1                                                                             
hazard.n_sources          2                                                                             
hazard.output_weight      35.0                                                                          
hostname                  tstation.gem.lan                                                              
require_epsilons          False                                                                         
========================= ==============================================================================

Slowest sources
---------------
========= ============ ============ ========= ========= =========
source_id source_class num_ruptures calc_time num_sites num_split
========= ============ ============ ========= ========= =========
1         PointSource  1            0.0       1         0        
2         PointSource  1            0.0       1         0        
========= ============ ============ ========= ========= =========

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
PointSource  0.0       2     
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ===== ========= ===== ===== =========
operation-duration mean  stddev    min   max   num_tasks
compute_ruptures   0.030 7.071E-04 0.030 0.031 2        
================== ===== ========= ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
managing sources               0.097     0.0       1     
total compute_ruptures         0.060     0.0       2     
saving ruptures                0.049     0.0       2     
setting event years            0.037     0.0       1     
store source_info              0.005     0.0       1     
reading composite source model 0.002     0.0       1     
making contexts                0.002     0.0       2     
reading site collection        5.841E-05 0.0       1     
============================== ========= ========= ======