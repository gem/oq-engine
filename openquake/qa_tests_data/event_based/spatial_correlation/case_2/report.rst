Probabilistic Event-Based QA Test with Spatial Correlation, case 2
==================================================================

============================================== ========================
gem-tstation:/home/michele/ssd/calc_80576.hdf5 Thu Jan 26 05:25:56 2017
engine_version                                 2.3.0-gitd31dc69        
hazardlib_version                              0.23.0-git4d14bee       
============================================== ========================

num_sites = 2, sitecol = 808 B

Parameters
----------
=============================== ===============================
calculation_mode                'event_based'                  
number_of_logic_tree_samples    0                              
maximum_distance                {'Active Shallow Crust': 200.0}
investigation_time              50.0                           
ses_per_logic_tree_path         150                            
truncation_level                None                           
rupture_mesh_spacing            2.0                            
complex_fault_mesh_spacing      2.0                            
width_of_mfd_bin                0.1                            
area_source_discretization      10.0                           
ground_motion_correlation_model 'JB2009'                       
random_seed                     123456789                      
master_seed                     0                              
=============================== ===============================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
source                  `source_model.xml <source_model.xml>`_                      
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ====== ====================================== =============== ================
smlt_path weight source_model_file                      gsim_logic_tree num_realizations
========= ====== ====================================== =============== ================
b1        1.000  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
========= ====== ====================================== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== =================== ========= ========== ==========
grp_id gsims               distances siteparams ruptparams
====== =================== ========= ========== ==========
0      BooreAtkinson2008() rjb       vs30       rake mag  
====== =================== ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)
  0,BooreAtkinson2008(): ['<0,b1~b1,w=1.0>']>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== =========== ============ ============
source_model     grp_id trt                  num_sources eff_ruptures tot_ruptures
================ ====== ==================== =========== ============ ============
source_model.xml 0      Active Shallow Crust 1           1            1           
================ ====== ==================== =========== ============ ============

Informational data
------------------
========================================= ============
compute_ruptures_max_received_per_task    364,564     
compute_ruptures_num_tasks                1           
compute_ruptures_sent.gsims               102         
compute_ruptures_sent.monitor             927         
compute_ruptures_sent.sources             1,319       
compute_ruptures_sent.src_filter          618         
compute_ruptures_tot_received             364,564     
hazard.input_weight                       0.100       
hazard.n_imts                             1           
hazard.n_levels                           1           
hazard.n_realizations                     1           
hazard.n_sites                            2           
hazard.n_sources                          1           
hazard.output_weight                      150         
hostname                                  gem-tstation
require_epsilons                          False       
========================================= ============

Specific information for event based
------------------------------------
======================== ======
Total number of ruptures 1     
Total number of events   22,566
Rupture multiplicity     22,566
======================== ======

Slowest sources
---------------
====== ========= ============ ============ ========= ========= =========
grp_id source_id source_class num_ruptures calc_time num_sites num_split
====== ========= ============ ============ ========= ========= =========
0      1         PointSource  1            0.0       2         0        
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
compute_ruptures   0.024 NaN    0.024 0.024 1        
================== ===== ====== ===== ===== =========

Slowest operations
------------------
================================ ========= ========= ======
operation                        time_sec  memory_mb counts
================================ ========= ========= ======
setting event years              0.315     0.0       1     
saving ruptures                  0.111     0.0       1     
total compute_ruptures           0.024     0.273     1     
reading composite source model   0.003     0.0       1     
managing sources                 0.002     0.0       1     
filtering composite source model 0.002     0.0       1     
filtering ruptures               6.111E-04 0.0       1     
store source_info                5.567E-04 0.0       1     
reading site collection          4.172E-05 0.0       1     
================================ ========= ========= ======