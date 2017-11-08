Event-based PSHA producing hazard curves only
=============================================

============== ===================
checksum32     3,219,914,866      
date           2017-11-08T18:07:24
engine_version 2.8.0-gite3d0f56   
============== ===================

num_sites = 1, num_imts = 1

Parameters
----------
=============================== ==================
calculation_mode                'event_based'     
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              50.0              
ses_per_logic_tree_path         300               
truncation_level                3.0               
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                0.2               
area_source_discretization      20.0              
ground_motion_correlation_model None              
random_seed                     42                
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
b11       0.600  simple(3)       3/3             
b12       0.400  simple(3)       3/3             
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

  <RlzsAssoc(size=6, rlzs=6)
  0,BooreAtkinson2008(): [0]
  0,CampbellBozorgnia2008(): [1]
  0,ChiouYoungs2008(): [2]
  1,BooreAtkinson2008(): [3]
  1,CampbellBozorgnia2008(): [4]
  1,ChiouYoungs2008(): [5]>

Number of ruptures per tectonic region type
-------------------------------------------
================= ====== ==================== =========== ============ ============
source_model      grp_id trt                  num_sources eff_ruptures tot_ruptures
================= ====== ==================== =========== ============ ============
source_model1.xml 0      Active Shallow Crust 1           2,456        2,456       
source_model2.xml 1      Active Shallow Crust 1           2,456        2,456       
================= ====== ==================== =========== ============ ============

============= =====
#TRT models   2    
#sources      2    
#eff_ruptures 4,912
#tot_ruptures 4,912
#tot_weight   0    
============= =====

Informational data
------------------
========================= ====================================================================================
compute_ruptures.received tot 2.53 MB, max_per_task 1.46 MB                                                   
compute_ruptures.sent     sources 163.71 KB, src_filter 2.67 KB, param 2.38 KB, monitor 1.27 KB, gsims 1.04 KB
hazard.input_weight       491.20000000000005                                                                  
hazard.n_imts             1                                                                                   
hazard.n_levels           5                                                                                   
hazard.n_realizations     6                                                                                   
hazard.n_sites            1                                                                                   
hazard.n_sources          2                                                                                   
hazard.output_weight      300.0                                                                               
hostname                  tstation.gem.lan                                                                    
require_epsilons          False                                                                               
========================= ====================================================================================

Slowest sources
---------------
====== ========= ============ ============ ========= ========= =========
grp_id source_id source_class num_ruptures calc_time num_sites num_split
====== ========= ============ ============ ========= ========= =========
0      1         AreaSource   2,456        0.0       1         0        
1      1         AreaSource   2,456        0.0       1         0        
====== ========= ============ ============ ========= ========= =========

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
AreaSource   0.0       2     
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
compute_ruptures   1.012 0.691  0.406 1.717 4        
================== ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total compute_ruptures         4.047     3.340     4     
filtering ruptures             0.719     0.0       3,081 
managing sources               0.190     0.0       1     
saving ruptures                0.130     0.0       4     
reading composite source model 0.113     0.0       1     
setting event years            0.075     0.0       1     
store source_info              0.004     0.0       1     
prefiltering source model      0.002     0.0       1     
reading site collection        4.077E-05 0.0       1     
============================== ========= ========= ======