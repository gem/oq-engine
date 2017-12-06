Event-based PSHA with logic tree sampling
=========================================

============== ===================
checksum32     3,756,725,912      
date           2017-12-06T11:20:40
engine_version 2.9.0-gite55e76e   
============== ===================

num_sites = 3, num_imts = 2

Parameters
----------
=============================== ==================
calculation_mode                'event_based'     
number_of_logic_tree_samples    10                
maximum_distance                {'default': 200.0}
investigation_time              50.0              
ses_per_logic_tree_path         40                
truncation_level                3.0               
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                0.2               
area_source_discretization      20.0              
ground_motion_correlation_model None              
random_seed                     23                
master_seed                     0                 
=============================== ==================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
source                  `source_model1.xml <source_model1.xml>`_                    
source                  `source_model2.xml <source_model2.xml>`_                    
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ====== =============== ================
smlt_path weight gsim_logic_tree num_realizations
========= ====== =============== ================
b11       0.100  simple(3)       4/3             
b12       0.100  simple(3)       6/3             
========= ====== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ============================================================= =========== ============================= =================
grp_id gsims                                                         distances   siteparams                    ruptparams       
====== ============================================================= =========== ============================= =================
0      BooreAtkinson2008() CampbellBozorgnia2008() ChiouYoungs2008() rjb rrup rx vs30 vs30measured z1pt0 z2pt5 dip mag rake ztor
1      BooreAtkinson2008() CampbellBozorgnia2008() ChiouYoungs2008() rjb rrup rx vs30 vs30measured z1pt0 z2pt5 dip mag rake ztor
====== ============================================================= =========== ============================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=5, rlzs=10)
  0,BooreAtkinson2008(): [1]
  0,CampbellBozorgnia2008(): [2]
  0,ChiouYoungs2008(): [0 3]
  1,BooreAtkinson2008(): [4 5 6 7 9]
  1,CampbellBozorgnia2008(): [8]>

Number of ruptures per tectonic region type
-------------------------------------------
================= ====== ==================== ============ ============
source_model      grp_id trt                  eff_ruptures tot_ruptures
================= ====== ==================== ============ ============
source_model1.xml 0      Active Shallow Crust 2,456        2,456       
source_model2.xml 1      Active Shallow Crust 2,456        2,456       
================= ====== ==================== ============ ============

============= =====
#TRT models   2    
#eff_ruptures 4,912
#tot_ruptures 4,912
#tot_weight   0    
============= =====

Informational data
------------------
========================= ======================================================================================
compute_ruptures.received tot 2.1 MB, max_per_task 369.45 KB                                                    
compute_ruptures.sent     sources 177.75 KB, param 12.84 KB, src_filter 10.12 KB, monitor 4.42 KB, gsims 3.65 KB
hazard.input_weight       2456.0                                                                                
hazard.n_imts             2                                                                                     
hazard.n_levels           38                                                                                    
hazard.n_realizations     10                                                                                    
hazard.n_sites            3                                                                                     
hazard.n_sources          2                                                                                     
hazard.output_weight      360.0                                                                                 
hostname                  tstation.gem.lan                                                                      
require_epsilons          False                                                                                 
========================= ======================================================================================

Slowest sources
---------------
========= ============ ============ ========= ========= =========
source_id source_class num_ruptures calc_time num_sites num_split
========= ============ ============ ========= ========= =========
1         AreaSource   2,456        0.0       1         0        
========= ============ ============ ========= ========= =========

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
AreaSource   0.0       1     
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
compute_ruptures   0.281 0.070  0.187 0.459 14       
================== ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total compute_ruptures         3.934     0.250     14    
managing sources               0.827     0.0       1     
filtering ruptures             0.736     0.0       2,667 
reading composite source model 0.214     0.0       1     
saving ruptures                0.165     0.0       14    
setting event years            0.041     0.0       1     
store source_info              0.004     0.0       1     
reading site collection        5.269E-05 0.0       1     
============================== ========= ========= ======