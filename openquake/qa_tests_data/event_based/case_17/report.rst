Event Based Hazard QA Test, Case 17
===================================

=============================================== ========================
tstation.gem.lan:/mnt/ssd/oqdata/calc_7619.hdf5 Wed Apr 26 15:55:49 2017
engine_version                                  2.4.0-git9336bd0        
hazardlib_version                               0.24.0-gita895d4c       
=============================================== ========================

num_sites = 1, sitecol = 809 B

Parameters
----------
=============================== ==================
calculation_mode                'event_based'     
number_of_logic_tree_samples    5                 
maximum_distance                {'default': 200.0}
investigation_time              1.0               
ses_per_logic_tree_path         3                 
truncation_level                2.0               
rupture_mesh_spacing            1.0               
complex_fault_mesh_spacing      1.0               
width_of_mfd_bin                1.0               
area_source_discretization      10.0              
ground_motion_correlation_model None              
random_seed                     106               
master_seed                     0                 
=============================== ==================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gsim_logic_tree.xml <gsim_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
source                  `source_model_1.xml <source_model_1.xml>`_                  
source                  `source_model_2.xml <source_model_2.xml>`_                  
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ====== ========================================== =============== ================
smlt_path weight source_model_file                          gsim_logic_tree num_realizations
========= ====== ========================================== =============== ================
b1        0.200  `source_model_1.xml <source_model_1.xml>`_ trivial(1)      1/0             
b2        0.200  `source_model_2.xml <source_model_2.xml>`_ trivial(1)      4/1             
========= ====== ========================================== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================ ========= ========== ==========
grp_id gsims            distances siteparams ruptparams
====== ================ ========= ========== ==========
1      SadighEtAl1997() rrup      vs30       rake mag  
====== ================ ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=5)
  1,SadighEtAl1997(): ['<1,b2~b1,w=0.2>', '<2,b2~b1,w=0.2>', '<3,b2~b1,w=0.2>', '<4,b2~b1,w=0.2>']>

Number of ruptures per tectonic region type
-------------------------------------------
================== ====== ==================== =========== ============ ============
source_model       grp_id trt                  num_sources eff_ruptures tot_ruptures
================== ====== ==================== =========== ============ ============
source_model_2.xml 1      Active Shallow Crust 1           3            7           
================== ====== ==================== =========== ============ ============

Informational data
------------------
============================ ==============================================================================
compute_ruptures.received    tot 6.08 KB, max_per_task 4.91 KB                                             
compute_ruptures.sent        sources 3.03 KB, monitor 1.66 KB, src_filter 1.34 KB, gsims 182 B, param 130 B
hazard.input_weight          6.700                                                                         
hazard.n_imts                1 B                                                                           
hazard.n_levels              3 B                                                                           
hazard.n_realizations        5 B                                                                           
hazard.n_sites               1 B                                                                           
hazard.n_sources             2 B                                                                           
hazard.output_weight         0.150                                                                         
hostname                     tstation.gem.lan                                                              
require_epsilons             0 B                                                                           
============================ ==============================================================================

Slowest sources
---------------
====== ========= ============ ============ ========= ========= =========
grp_id source_id source_class num_ruptures calc_time num_sites num_split
====== ========= ============ ============ ========= ========= =========
0      1         PointSource  39           0.0       1         0        
1      2         PointSource  7            0.0       1         0        
====== ========= ============ ============ ========= ========= =========

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
PointSource  0.0       2     
============ ========= ======

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
compute_ruptures   0.016 0.012  0.007 0.025 2        
================== ===== ====== ===== ===== =========

Slowest operations
------------------
================================ ========= ========= ======
operation                        time_sec  memory_mb counts
================================ ========= ========= ======
total compute_ruptures           0.032     0.0       2     
reading composite source model   0.004     0.0       1     
saving ruptures                  0.004     0.0       2     
filtering composite source model 0.002     0.0       1     
setting event years              0.002     0.0       1     
filtering ruptures               0.001     0.0       3     
store source_info                6.695E-04 0.0       1     
managing sources                 1.390E-04 0.0       1     
reading site collection          5.627E-05 0.0       1     
================================ ========= ========= ======