QA test for blocksize independence (hazard)
===========================================

============================================ ========================
gem-tstation:/mnt/ssd/oqdata/calc_85589.hdf5 Tue Feb 14 15:48:29 2017
engine_version                               2.3.0-git1f56df2        
hazardlib_version                            0.23.0-git6937706       
============================================ ========================

num_sites = 2, sitecol = 863 B

Parameters
----------
=============================== ==================
calculation_mode                'event_based'     
number_of_logic_tree_samples    1                 
maximum_distance                {'default': 400.0}
investigation_time              5.0               
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            10.0              
complex_fault_mesh_spacing      10.0              
width_of_mfd_bin                0.5               
area_source_discretization      10.0              
ground_motion_correlation_model None              
random_seed                     1024              
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
====== ================= =========== ======================= =================
grp_id gsims             distances   siteparams              ruptparams       
====== ================= =========== ======================= =================
0      ChiouYoungs2008() rrup rjb rx vs30 z1pt0 vs30measured ztor mag rake dip
====== ================= =========== ======================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)
  0,ChiouYoungs2008(): ['<0,b1~b1,w=1.0>']>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== =========== ============ ============
source_model     grp_id trt                  num_sources eff_ruptures tot_ruptures
================ ====== ==================== =========== ============ ============
source_model.xml 0      Active Shallow Crust 5           3            13,823      
================ ====== ==================== =========== ============ ============

Informational data
------------------
========================================= ============
compute_ruptures_max_received_per_task    8,804       
compute_ruptures_num_tasks                9           
compute_ruptures_sent.gsims               882         
compute_ruptures_sent.monitor             9,549       
compute_ruptures_sent.sources             436,439     
compute_ruptures_sent.src_filter          6,642       
compute_ruptures_tot_received             41,538      
hazard.input_weight                       1,382       
hazard.n_imts                             1           
hazard.n_levels                           4           
hazard.n_realizations                     1           
hazard.n_sites                            2           
hazard.n_sources                          5           
hazard.output_weight                      0.100       
hostname                                  gem-tstation
require_epsilons                          False       
========================================= ============

Specific information for event based
------------------------------------
======================== =====
Total number of ruptures 3    
Total number of events   3    
Rupture multiplicity     1.000
======================== =====

Slowest sources
---------------
====== ========= ============ ============ ========= ========= =========
grp_id source_id source_class num_ruptures calc_time num_sites num_split
====== ========= ============ ============ ========= ========= =========
0      2         AreaSource   2,334        0.0       2         0        
0      1         AreaSource   7,020        0.0       2         0        
0      3         AreaSource   1,760        0.0       2         0        
0      8         AreaSource   1,812        0.0       1         0        
0      9         AreaSource   897          0.0       2         0        
====== ========= ============ ============ ========= ========= =========

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
AreaSource   0.0       5     
============ ========= ======

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
compute_ruptures   0.419 0.301  0.003 0.703 9        
================== ===== ====== ===== ===== =========

Slowest operations
------------------
================================ ========= ========= ======
operation                        time_sec  memory_mb counts
================================ ========= ========= ======
total compute_ruptures           3.771     0.0       9     
reading composite source model   1.677     0.0       1     
managing sources                 1.298     0.0       1     
saving ruptures                  0.006     0.0       9     
filtering composite source model 0.005     0.0       1     
setting event years              0.002     0.0       1     
filtering ruptures               0.001     0.0       3     
store source_info                8.802E-04 0.0       1     
reading site collection          4.268E-05 0.0       1     
================================ ========= ========= ======