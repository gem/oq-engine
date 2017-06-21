event based risk
================

================================================ ========================
tstation.gem.lan:/mnt/ssd/oqdata/calc_29208.hdf5 Wed Jun 14 10:03:55 2017
engine_version                                   2.5.0-gite200a20        
================================================ ========================

num_sites = 7, num_imts = 1

Parameters
----------
=============================== ==================
calculation_mode                'event_based_risk'
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              10000.0           
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                0.1               
area_source_discretization      None              
ground_motion_correlation_model 'JB2009'          
random_seed                     24                
master_seed                     42                
avg_losses                      False             
=============================== ==================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
exposure                `exposure_model.xml <exposure_model.xml>`_                  
gsim_logic_tree         `gsim_logic_tree.xml <gsim_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
occupants_vulnerability `vulnerability_model.xml <vulnerability_model.xml>`_        
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
source_model.xml 0      Active Shallow Crust 1           482          482         
================ ====== ==================== =========== ============ ============

Informational data
------------------
============================ =============================================================================
compute_ruptures.received    tot 233.71 KB, max_per_task 84.44 KB                                         
compute_ruptures.sent        sources 7.78 KB, src_filter 2.5 KB, param 1.61 KB, monitor 933 B, gsims 306 B
hazard.input_weight          482                                                                          
hazard.n_imts                1 B                                                                          
hazard.n_levels              1 B                                                                          
hazard.n_realizations        1 B                                                                          
hazard.n_sites               7 B                                                                          
hazard.n_sources             1 B                                                                          
hazard.output_weight         7.000                                                                        
hostname                     tstation.gem.lan                                                             
require_epsilons             1 B                                                                          
============================ =============================================================================

Estimated data transfer for the avglosses
-----------------------------------------
7 asset(s) x 1 realization(s) x 1 loss type(s) x 1 losses x 8 bytes x 50 tasks = 2.73 KB

Exposure model
--------------
=============== ========
#assets         7       
#taxonomies     1       
deductibile     absolute
insurance_limit absolute
=============== ========

======== ===== ====== === === ========= ==========
taxonomy mean  stddev min max num_sites num_assets
tax1     1.000 0.0    1   1   7         7         
======== ===== ====== === === ========= ==========

Slowest sources
---------------
====== ========= ================= ============ ========= ========= =========
grp_id source_id source_class      num_ruptures calc_time num_sites num_split
====== ========= ================= ============ ========= ========= =========
0      1         SimpleFaultSource 482          0.0       7         0        
====== ========= ================= ============ ========= ========= =========

Computation times by source typology
------------------------------------
================= ========= ======
source_class      calc_time counts
================= ========= ======
SimpleFaultSource 0.0       1     
================= ========= ======

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
compute_ruptures   0.088 0.017  0.072 0.105 3        
================== ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total compute_ruptures         0.264     0.758     3     
filtering ruptures             0.087     0.0       259   
managing sources               0.058     0.0       1     
saving ruptures                0.014     0.0       3     
reading exposure               0.008     0.0       1     
reading composite source model 0.004     0.0       1     
store source_info              0.004     0.0       1     
setting event years            0.003     0.0       1     
prefiltering source model      0.002     0.0       1     
reading site collection        8.345E-06 0.0       1     
============================== ========= ========= ======