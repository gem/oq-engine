QA test for blocksize independence (hazard)
===========================================

============================================== ========================
gem-tstation:/home/michele/ssd/calc_80583.hdf5 Thu Jan 26 05:26:09 2017
engine_version                                 2.3.0-gitd31dc69        
hazardlib_version                              0.23.0-git4d14bee       
============================================== ========================

num_sites = 2, sitecol = 808 B

Parameters
----------
=============================== ===============================
calculation_mode                'event_based'                  
number_of_logic_tree_samples    1                              
maximum_distance                {'Active Shallow Crust': 400.0}
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
====== ================= =========== ======================= =================
grp_id gsims             distances   siteparams              ruptparams       
====== ================= =========== ======================= =================
0      ChiouYoungs2008() rrup rx rjb z1pt0 vs30 vs30measured dip rake mag ztor
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
compute_ruptures_max_received_per_task    8,741       
compute_ruptures_num_tasks                9           
compute_ruptures_sent.gsims               882         
compute_ruptures_sent.monitor             8,982       
compute_ruptures_sent.sources             436,439     
compute_ruptures_sent.src_filter          5,562       
compute_ruptures_tot_received             40,965      
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
0      1         AreaSource   7,020        0.0       2         0        
0      2         AreaSource   2,334        0.0       2         0        
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
compute_ruptures   0.412 0.300  0.003 0.698 9        
================== ===== ====== ===== ===== =========

Slowest operations
------------------
================================ ========= ========= ======
operation                        time_sec  memory_mb counts
================================ ========= ========= ======
total compute_ruptures           3.705     0.0       9     
reading composite source model   1.648     0.0       1     
managing sources                 1.345     0.0       1     
split/filter heavy sources       1.340     0.0       1     
saving ruptures                  0.007     0.0       9     
filtering composite source model 0.005     0.0       1     
setting event years              0.003     0.0       1     
store source_info                0.001     0.0       1     
filtering ruptures               9.835E-04 0.0       3     
reading site collection          4.125E-05 0.0       1     
================================ ========= ========= ======