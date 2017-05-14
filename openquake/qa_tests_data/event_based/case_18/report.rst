Event-Based Hazard QA Test, Case 18
===================================

================================================ ========================
tstation.gem.lan:/mnt/ssd/oqdata/calc_21353.hdf5 Fri May 12 10:46:12 2017
engine_version                                   2.4.0-git59713b5        
hazardlib_version                                0.24.0-git0596dd3       
================================================ ========================

num_sites = 1, sitecol = 809 B

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
0      AkkarBommer2010() CauzziFaccioli2008() rhypo rjb vs30       mag rake  
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
============================ ==========================================================================
compute_ruptures.received    tot 6.85 KB, max_per_task 6.85 KB                                         
compute_ruptures.sent        sources 13.01 KB, monitor 858 B, src_filter 684 B, gsims 181 B, param 67 B
hazard.input_weight          900                                                                       
hazard.n_imts                1 B                                                                       
hazard.n_levels              4 B                                                                       
hazard.n_realizations        3 B                                                                       
hazard.n_sites               1 B                                                                       
hazard.n_sources             1 B                                                                       
hazard.output_weight         3.500                                                                     
hostname                     tstation.gem.lan                                                          
require_epsilons             0 B                                                                       
============================ ==========================================================================

Slowest sources
---------------
====== ========= ============ ============ ========= ========= =========
grp_id source_id source_class num_ruptures calc_time num_sites num_split
====== ========= ============ ============ ========= ========= =========
0      1         PointSource  3,000        0.0       0         0        
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
compute_ruptures   3.810 NaN    3.810 3.810 1        
================== ===== ====== ===== ===== =========

Slowest operations
------------------
================================ ========= ========= ======
operation                        time_sec  memory_mb counts
================================ ========= ========= ======
total compute_ruptures           3.810     0.0       1     
saving ruptures                  0.006     0.0       1     
reading composite source model   0.005     0.0       1     
setting event years              0.002     0.0       1     
filtering ruptures               0.001     0.0       6     
store source_info                0.001     0.0       1     
managing sources                 7.546E-04 0.0       1     
filtering composite source model 3.505E-05 0.0       1     
reading site collection          3.147E-05 0.0       1     
================================ ========= ========= ======