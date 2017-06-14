Probabilistic Event-Based QA Test with Spatial Correlation, case 2
==================================================================

================================================ ========================
tstation.gem.lan:/mnt/ssd/oqdata/calc_29250.hdf5 Wed Jun 14 10:04:46 2017
engine_version                                   2.5.0-gite200a20        
================================================ ========================

num_sites = 2, num_imts = 1

Parameters
----------
=============================== ==================
calculation_mode                'event_based'     
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              50.0              
ses_per_logic_tree_path         150               
truncation_level                None              
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                0.1               
area_source_discretization      10.0              
ground_motion_correlation_model 'JB2009'          
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
0      BooreAtkinson2008() rjb       vs30       mag rake  
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
============================ ==========================================================================
compute_ruptures.received    max_per_task 354.99 KB, tot 354.99 KB                                     
compute_ruptures.sent        sources 1.29 KB, src_filter 712 B, param 544 B, monitor 311 B, gsims 102 B
hazard.input_weight          0.100                                                                     
hazard.n_imts                1 B                                                                       
hazard.n_levels              1 B                                                                       
hazard.n_realizations        1 B                                                                       
hazard.n_sites               2 B                                                                       
hazard.n_sources             1 B                                                                       
hazard.output_weight         150                                                                       
hostname                     tstation.gem.lan                                                          
require_epsilons             0 B                                                                       
============================ ==========================================================================

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
compute_ruptures   0.019 NaN    0.019 0.019 1        
================== ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
setting event years            0.099     0.0       1     
saving ruptures                0.088     0.0       1     
total compute_ruptures         0.019     0.422     1     
store source_info              0.005     0.0       1     
reading composite source model 0.001     0.0       1     
managing sources               9.508E-04 0.0       1     
filtering ruptures             5.510E-04 0.0       1     
prefiltering source model      4.990E-04 0.0       1     
reading site collection        3.791E-05 0.0       1     
============================== ========= ========= ======