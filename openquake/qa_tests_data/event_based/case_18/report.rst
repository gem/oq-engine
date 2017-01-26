Event-Based Hazard QA Test, Case 18
===================================

============================================== ========================
gem-tstation:/home/michele/ssd/calc_80581.hdf5 Thu Jan 26 05:26:02 2017
engine_version                                 2.3.0-gitd31dc69        
hazardlib_version                              0.23.0-git4d14bee       
============================================== ========================

num_sites = 1, sitecol = 762 B

Parameters
----------
=============================== ===============================
calculation_mode                'event_based'                  
number_of_logic_tree_samples    3                              
maximum_distance                {'active shallow crust': 200.0}
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
=============================== ===============================

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
========= ====== ====================================== =============== ================
smlt_path weight source_model_file                      gsim_logic_tree num_realizations
========= ====== ====================================== =============== ================
b1        0.333  `source_model.xml <source_model.xml>`_ simple(3)       3/3             
========= ====== ====================================== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ====================================== ========= ========== ==========
grp_id gsims                                  distances siteparams ruptparams
====== ====================================== ========= ========== ==========
0      AkkarBommer2010() CauzziFaccioli2008() rhypo rjb vs30       rake mag  
====== ====================================== ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=2, rlzs=3)
  0,AkkarBommer2010(): ['<0,b1~AB,w=0.333333333333>', '<1,b1~AB,w=0.333333333333>']
  0,CauzziFaccioli2008(): ['<2,b1~CF,w=0.333333333333>']>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== =========== ============ ============
source_model     grp_id trt                  num_sources eff_ruptures tot_ruptures
================ ====== ==================== =========== ============ ============
source_model.xml 0      Active Shallow Crust 1           6            3,000       
================ ====== ==================== =========== ============ ============

Informational data
------------------
========================================= ============
compute_ruptures_max_received_per_task    8,455       
compute_ruptures_num_tasks                1           
compute_ruptures_sent.gsims               181         
compute_ruptures_sent.monitor             999         
compute_ruptures_sent.sources             13,336      
compute_ruptures_sent.src_filter          598         
compute_ruptures_tot_received             8,455       
hazard.input_weight                       900         
hazard.n_imts                             1           
hazard.n_levels                           4           
hazard.n_realizations                     3           
hazard.n_sites                            1           
hazard.n_sources                          1           
hazard.output_weight                      10          
hostname                                  gem-tstation
require_epsilons                          False       
========================================= ============

Specific information for event based
------------------------------------
======================== =====
Total number of ruptures 6    
Total number of events   6    
Rupture multiplicity     1.000
======================== =====

Slowest sources
---------------
====== ========= ============ ============ ========= ========= =========
grp_id source_id source_class num_ruptures calc_time num_sites num_split
====== ========= ============ ============ ========= ========= =========
0      1         PointSource  3,000        0.0       1         0        
====== ========= ============ ============ ========= ========= =========

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
PointSource  0.0       1     
============ ========= ======

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
compute_ruptures   3.130 NaN    3.130 3.130 1        
================== ===== ====== ===== ===== =========

Slowest operations
------------------
================================ ========= ========= ======
operation                        time_sec  memory_mb counts
================================ ========= ========= ======
total compute_ruptures           3.130     0.0       1     
reading composite source model   0.014     0.0       1     
filtering composite source model 0.011     0.0       1     
managing sources                 0.005     0.0       1     
saving ruptures                  0.004     0.0       1     
split/filter heavy sources       0.003     0.0       1     
setting event years              0.002     0.0       1     
filtering ruptures               0.001     0.0       6     
store source_info                9.224E-04 0.0       1     
reading site collection          4.077E-05 0.0       1     
================================ ========= ========= ======