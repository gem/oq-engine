Event Based Hazard QA Test, Case 17
===================================

============================================ ========================
gem-tstation:/mnt/ssd/oqdata/calc_85578.hdf5 Tue Feb 14 15:48:12 2017
engine_version                               2.3.0-git1f56df2        
hazardlib_version                            0.23.0-git6937706       
============================================ ========================

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
1      SadighEtAl1997() rrup      vs30       mag rake  
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
========================================= ============
compute_ruptures_max_received_per_task    5,958       
compute_ruptures_num_tasks                2           
compute_ruptures_sent.gsims               182         
compute_ruptures_sent.monitor             2,106       
compute_ruptures_sent.sources             3,101       
compute_ruptures_sent.src_filter          1,420       
compute_ruptures_tot_received             7,838       
hazard.input_weight                       6.700       
hazard.n_imts                             1           
hazard.n_levels                           3           
hazard.n_realizations                     5           
hazard.n_sites                            1           
hazard.n_sources                          2           
hazard.output_weight                      0.150       
hostname                                  gem-tstation
require_epsilons                          False       
========================================= ============

Specific information for event based
------------------------------------
======================== =====
Total number of ruptures 3    
Total number of events   23   
Rupture multiplicity     7.667
======================== =====

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
compute_ruptures   0.014 0.010  0.007 0.022 2        
================== ===== ====== ===== ===== =========

Slowest operations
------------------
================================ ========= ========= ======
operation                        time_sec  memory_mb counts
================================ ========= ========= ======
total compute_ruptures           0.029     0.0       2     
saving ruptures                  0.018     0.0       2     
reading composite source model   0.006     0.0       1     
filtering composite source model 0.003     0.0       1     
managing sources                 0.003     0.0       1     
setting event years              0.002     0.0       1     
filtering ruptures               0.001     0.0       3     
store source_info                7.811E-04 0.0       1     
reading site collection          5.078E-05 0.0       1     
================================ ========= ========= ======