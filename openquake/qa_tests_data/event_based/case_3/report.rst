Event Based QA Test, Case 3
===========================

============================================ ========================
gem-tstation:/mnt/ssd/oqdata/calc_85584.hdf5 Tue Feb 14 15:48:18 2017
engine_version                               2.3.0-git1f56df2        
hazardlib_version                            0.23.0-git6937706       
============================================ ========================

num_sites = 1, sitecol = 809 B

Parameters
----------
=============================== ==================
calculation_mode                'event_based'     
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              2.0               
ses_per_logic_tree_path         1                 
truncation_level                2.0               
rupture_mesh_spacing            1.0               
complex_fault_mesh_spacing      1.0               
width_of_mfd_bin                1.0               
area_source_discretization      10.0              
ground_motion_correlation_model None              
random_seed                     1066              
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
b1        1.000  `source_model.xml <source_model.xml>`_ simple(2)       2/2             
========= ====== ====================================== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================================== ========= ========== ==========
grp_id gsims                              distances siteparams ruptparams
====== ================================== ========= ========== ==========
0      AkkarBommer2010() SadighEtAl1997() rrup rjb  vs30       mag rake  
====== ================================== ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=2, rlzs=2)
  0,AkkarBommer2010(): ['<1,b1~b2,w=0.4>']
  0,SadighEtAl1997(): ['<0,b1~b1,w=0.6>']>

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
compute_ruptures_max_received_per_task    3,702       
compute_ruptures_num_tasks                1           
compute_ruptures_sent.gsims               168         
compute_ruptures_sent.monitor             1,053       
compute_ruptures_sent.sources             1,325       
compute_ruptures_sent.src_filter          710         
compute_ruptures_tot_received             3,702       
hazard.input_weight                       0.100       
hazard.n_imts                             1           
hazard.n_levels                           3           
hazard.n_realizations                     2           
hazard.n_sites                            1           
hazard.n_sources                          1           
hazard.output_weight                      0.040       
hostname                                  gem-tstation
require_epsilons                          False       
========================================= ============

Specific information for event based
------------------------------------
======================== =====
Total number of ruptures 1    
Total number of events   2    
Rupture multiplicity     2.000
======================== =====

Slowest sources
---------------
====== ========= ============ ============ ========= ========= =========
grp_id source_id source_class num_ruptures calc_time num_sites num_split
====== ========= ============ ============ ========= ========= =========
0      1         PointSource  1            0.0       1         0        
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
compute_ruptures   0.002 NaN    0.002 0.002 1        
================== ===== ====== ===== ===== =========

Slowest operations
------------------
================================ ========= ========= ======
operation                        time_sec  memory_mb counts
================================ ========= ========= ======
reading composite source model   0.003     0.0       1     
saving ruptures                  0.003     0.0       1     
total compute_ruptures           0.002     0.0       1     
setting event years              0.002     0.0       1     
filtering composite source model 0.002     0.0       1     
managing sources                 0.002     0.0       1     
store source_info                7.923E-04 0.0       1     
filtering ruptures               5.045E-04 0.0       1     
reading site collection          4.005E-05 0.0       1     
================================ ========= ========= ======