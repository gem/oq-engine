Event-based PSHA producing hazard curves only
=============================================

================================================ ========================
tstation.gem.lan:/mnt/ssd/oqdata/calc_29248.hdf5 Wed Jun 14 10:04:46 2017
engine_version                                   2.5.0-gite200a20        
================================================ ========================

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
========= ====== ======================================== =============== ================
smlt_path weight source_model_file                        gsim_logic_tree num_realizations
========= ====== ======================================== =============== ================
b11       0.600  `source_model1.xml <source_model1.xml>`_ simple(3)       3/3             
b12       0.400  `source_model2.xml <source_model2.xml>`_ simple(3)       3/3             
========= ====== ======================================== =============== ================

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
  0,BooreAtkinson2008(): ['<0,b11~b11,w=0.30000000298023216>']
  0,CampbellBozorgnia2008(): ['<1,b11~b12,w=0.1800000017881393>']
  0,ChiouYoungs2008(): ['<2,b11~b13,w=0.12000000119209286>']
  1,BooreAtkinson2008(): ['<3,b12~b11,w=0.19999999701976784>']
  1,CampbellBozorgnia2008(): ['<4,b12~b12,w=0.1199999982118607>']
  1,ChiouYoungs2008(): ['<5,b12~b13,w=0.07999999880790715>']>

Number of ruptures per tectonic region type
-------------------------------------------
================= ====== ==================== =========== ============ ============
source_model      grp_id trt                  num_sources eff_ruptures tot_ruptures
================= ====== ==================== =========== ============ ============
source_model1.xml 0      Active Shallow Crust 1           2456         2,456       
source_model2.xml 1      Active Shallow Crust 1           2456         2,456       
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
============================ ====================================================================================
compute_ruptures.received    tot 2.53 MB, max_per_task 1.46 MB                                                   
compute_ruptures.sent        sources 163.66 KB, src_filter 2.67 KB, param 2.43 KB, monitor 1.21 KB, gsims 1.04 KB
hazard.input_weight          491                                                                                 
hazard.n_imts                1 B                                                                                 
hazard.n_levels              5 B                                                                                 
hazard.n_realizations        6 B                                                                                 
hazard.n_sites               1 B                                                                                 
hazard.n_sources             2 B                                                                                 
hazard.output_weight         300                                                                                 
hostname                     tstation.gem.lan                                                                    
require_epsilons             0 B                                                                                 
============================ ====================================================================================

Slowest sources
---------------
====== ========= ============ ============ ========= ========= =========
grp_id source_id source_class num_ruptures calc_time num_sites num_split
====== ========= ============ ============ ========= ========= =========
1      1         AreaSource   2,456        0.0       1         0        
0      1         AreaSource   2,456        0.0       1         0        
====== ========= ============ ============ ========= ========= =========

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
AreaSource   0.0       2     
============ ========= ======

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
compute_ruptures   0.982 0.683  0.347 1.698 4        
================== ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total compute_ruptures         3.929     2.348     4     
filtering ruptures             0.702     0.0       3,081 
managing sources               0.194     0.0       1     
reading composite source model 0.115     0.0       1     
saving ruptures                0.107     0.0       4     
setting event years            0.056     0.0       1     
store source_info              0.004     0.0       1     
prefiltering source model      0.002     0.0       1     
reading site collection        4.554E-05 0.0       1     
============================== ========= ========= ======