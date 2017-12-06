Event-Based Hazard QA Test, Case 18
===================================

============== ===================
checksum32     2,067,964,765      
date           2017-12-06T11:20:35
engine_version 2.9.0-gite55e76e   
============== ===================

num_sites = 1, num_imts = 1

Parameters
----------
=============================== ==================
calculation_mode                'event_based'     
number_of_logic_tree_samples    3                 
maximum_distance                {'default': 200.0}
investigation_time              1.0               
ses_per_logic_tree_path         350               
truncation_level                0.0               
rupture_mesh_spacing            1.0               
complex_fault_mesh_spacing      1.0               
width_of_mfd_bin                0.001             
area_source_discretization      10.0              
ground_motion_correlation_model None              
random_seed                     1064              
master_seed                     0                 
=============================== ==================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `three_gsim_logic_tree.xml <three_gsim_logic_tree.xml>`_    
job_ini                 `job.ini <job.ini>`_                                        
source                  `source_model.xml <source_model.xml>`_                      
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ====== =============== ================
smlt_path weight gsim_logic_tree num_realizations
========= ====== =============== ================
b1        0.333  simple(3)       3/3             
========= ====== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ======================================================== ================= ======================= =================
grp_id gsims                                                    distances         siteparams              ruptparams       
====== ======================================================== ================= ======================= =================
0      AkkarBommer2010() CauzziFaccioli2008() ChiouYoungs2008() rhypo rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
====== ======================================================== ================= ======================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=2, rlzs=3)
  0,AkkarBommer2010(): [0 2]
  0,ChiouYoungs2008(): [1]>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== ============ ============
source_model     grp_id trt                  eff_ruptures tot_ruptures
================ ====== ==================== ============ ============
source_model.xml 0      Active Shallow Crust 3,000        3,000       
================ ====== ==================== ============ ============

Informational data
------------------
========================= ===========================================================================
compute_ruptures.received max_per_task 6.44 KB, tot 6.44 KB                                          
compute_ruptures.sent     sources 13.05 KB, src_filter 684 B, param 591 B, monitor 323 B, gsims 257 B
hazard.input_weight       900.0                                                                      
hazard.n_imts             1                                                                          
hazard.n_levels           4                                                                          
hazard.n_realizations     3                                                                          
hazard.n_sites            1                                                                          
hazard.n_sources          1                                                                          
hazard.output_weight      3.5                                                                        
hostname                  tstation.gem.lan                                                           
require_epsilons          False                                                                      
========================= ===========================================================================

Slowest sources
---------------
========= ============ ============ ========= ========= =========
source_id source_class num_ruptures calc_time num_sites num_split
========= ============ ============ ========= ========= =========
1         PointSource  3,000        0.0       1         0        
========= ============ ============ ========= ========= =========

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
PointSource  0.0       1     
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
compute_ruptures   3.961 NaN    3.961 3.961 1        
================== ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
managing sources               3.982     0.0       1     
total compute_ruptures         3.961     0.0       1     
reading composite source model 0.009     0.0       1     
store source_info              0.006     0.0       1     
saving ruptures                0.005     0.0       1     
setting event years            0.002     0.0       1     
filtering ruptures             0.001     0.0       6     
reading site collection        3.171E-05 0.0       1     
============================== ========= ========= ======