Event-Based Hazard QA Test, Case 4
==================================

=============================================== ========================
tstation.gem.lan:/mnt/ssd/oqdata/calc_7627.hdf5 Wed Apr 26 15:55:53 2017
engine_version                                  2.4.0-git9336bd0        
hazardlib_version                               0.24.0-gita895d4c       
=============================================== ========================

num_sites = 1, sitecol = 809 B

Parameters
----------
=============================== ==================
calculation_mode                'event_based'     
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              1.0               
ses_per_logic_tree_path         50                
truncation_level                0.0               
rupture_mesh_spacing            1.0               
complex_fault_mesh_spacing      1.0               
width_of_mfd_bin                1.0               
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
0      SadighEtAl1997() rrup      vs30       rake mag  
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
source_model.xml 0      Active Shallow Crust 1           10           10          
================ ====== ==================== =========== ============ ============

Informational data
------------------
============================ ========================================================================
compute_ruptures.received    tot 7.98 KB, max_per_task 7.98 KB                                       
compute_ruptures.sent        sources 1.23 KB, monitor 849 B, src_filter 684 B, gsims 91 B, param 66 B
hazard.input_weight          10                                                                      
hazard.n_imts                1 B                                                                     
hazard.n_levels              3 B                                                                     
hazard.n_realizations        1 B                                                                     
hazard.n_sites               1 B                                                                     
hazard.n_sources             1 B                                                                     
hazard.output_weight         0.500                                                                   
hostname                     tstation.gem.lan                                                        
require_epsilons             0 B                                                                     
============================ ========================================================================

Slowest sources
---------------
====== ========= ================= ============ ========= ========= =========
grp_id source_id source_class      num_ruptures calc_time num_sites num_split
====== ========= ================= ============ ========= ========= =========
0      1         SimpleFaultSource 10           0.0       1         0        
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
compute_ruptures   0.015 NaN    0.015 0.015 1        
================== ===== ====== ===== ===== =========

Slowest operations
------------------
================================ ========= ========= ======
operation                        time_sec  memory_mb counts
================================ ========= ========= ======
total compute_ruptures           0.015     0.0       1     
reading composite source model   0.003     0.0       1     
saving ruptures                  0.002     0.0       1     
filtering ruptures               0.002     0.0       10    
setting event years              0.002     0.0       1     
filtering composite source model 0.001     0.0       1     
store source_info                4.616E-04 0.0       1     
managing sources                 8.368E-05 0.0       1     
reading site collection          3.147E-05 0.0       1     
================================ ========= ========= ======