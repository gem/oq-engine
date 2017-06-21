Event-Based Hazard QA Test, Case 2
==================================

================================================ ========================
tstation.gem.lan:/mnt/ssd/oqdata/calc_29246.hdf5 Wed Jun 14 10:04:43 2017
engine_version                                   2.5.0-gite200a20        
================================================ ========================

num_sites = 1, num_imts = 1

Parameters
----------
=============================== ==================
calculation_mode                'event_based'     
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              1.0               
ses_per_logic_tree_path         600               
truncation_level                0.0               
rupture_mesh_spacing            1.0               
complex_fault_mesh_spacing      1.0               
width_of_mfd_bin                0.001             
area_source_discretization      10.0              
ground_motion_correlation_model None              
random_seed                     42                
master_seed                     0                 
=============================== ==================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gsim_logic_tree.xml <gsim_logic_tree.xml>`_                
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
====== ================ ========= ========== ==========
grp_id gsims            distances siteparams ruptparams
====== ================ ========= ========== ==========
0      SadighEtAl1997() rrup      vs30       mag rake  
====== ================ ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)
  0,SadighEtAl1997(): ['<0,b1~b1,w=1.0>']>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== =========== ============ ============
source_model     grp_id trt                  num_sources eff_ruptures tot_ruptures
================ ====== ==================== =========== ============ ============
source_model.xml 0      Active Shallow Crust 1           3000         3,000       
================ ====== ==================== =========== ============ ============

Informational data
------------------
============================ ==========================================================================
compute_ruptures.received    max_per_task 4.02 KB, tot 4.02 KB                                         
compute_ruptures.sent        sources 13.02 KB, src_filter 684 B, param 614 B, monitor 311 B, gsims 91 B
hazard.input_weight          300                                                                       
hazard.n_imts                1 B                                                                       
hazard.n_levels              4 B                                                                       
hazard.n_realizations        1 B                                                                       
hazard.n_sites               1 B                                                                       
hazard.n_sources             1 B                                                                       
hazard.output_weight         6.000                                                                     
hostname                     tstation.gem.lan                                                          
require_epsilons             0 B                                                                       
============================ ==========================================================================

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
compute_ruptures   2.719 NaN    2.719 2.719 1        
================== ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total compute_ruptures         2.719     0.0       1     
store source_info              0.007     0.0       1     
reading composite source model 0.006     0.0       1     
saving ruptures                0.005     0.0       1     
prefiltering source model      0.004     0.0       1     
setting event years            0.002     0.0       1     
managing sources               0.001     0.0       1     
filtering ruptures             6.030E-04 0.0       3     
reading site collection        4.458E-05 0.0       1     
============================== ========= ========= ======