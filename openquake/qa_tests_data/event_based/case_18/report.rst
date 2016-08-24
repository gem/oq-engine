Event-Based Hazard QA Test, Case 18
===================================

thinkpad:/home/michele/oqdata/calc_16916.hdf5 updated Wed Aug 24 04:50:00 2016

num_sites = 1, sitecol = 739 B

Parameters
----------
============================ ================================
calculation_mode             'event_based'                   
number_of_logic_tree_samples 3                               
maximum_distance             {u'active shallow crust': 200.0}
investigation_time           1.0                             
ses_per_logic_tree_path      350                             
truncation_level             0.0                             
rupture_mesh_spacing         1.0                             
complex_fault_mesh_spacing   1.0                             
width_of_mfd_bin             0.001                           
area_source_discretization   10.0                            
random_seed                  1064                            
master_seed                  0                               
engine_version               '2.1.0-git74bd74a'              
============================ ================================

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
0      AkkarBommer2010() CauzziFaccioli2008() rhypo rjb vs30       rake mag  
====== ====================================== ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=2, rlzs=3)
  0,AkkarBommer2010(): ['<0,b1~AB,w=0.333333333333>', '<1,b1~AB,w=0.333333333333>']
  0,CauzziFaccioli2008(): ['<2,b1~CF,w=0.333333333333>']>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== =========== ============ ======
source_model     grp_id trt                  num_sources eff_ruptures weight
================ ====== ==================== =========== ============ ======
source_model.xml 0      Active Shallow Crust 1           6            75    
================ ====== ==================== =========== ============ ======

Informational data
------------------
====================================== ========
compute_ruptures_max_received_per_task 7,239   
compute_ruptures_num_tasks             1       
compute_ruptures_sent.monitor          821     
compute_ruptures_sent.rlzs_by_gsim     802     
compute_ruptures_sent.sitecol          433     
compute_ruptures_sent.sources          13,340  
compute_ruptures_tot_received          7,239   
hazard.input_weight                    225     
hazard.n_imts                          1       
hazard.n_levels                        4.000   
hazard.n_realizations                  3       
hazard.n_sites                         1       
hazard.n_sources                       1       
hazard.output_weight                   10      
hostname                               thinkpad
====================================== ========

Specific information for event based
------------------------------------
======================== =====
Total number of ruptures 6    
Total number of events   6    
Rupture multiplicity     1.000
======================== =====

Slowest sources
---------------
============ ========= ============ ====== ========= =========== ========== ============= ============= =========
src_group_id source_id source_class weight split_num filter_time split_time cum_calc_time max_calc_time num_tasks
============ ========= ============ ====== ========= =========== ========== ============= ============= =========
0            1         PointSource  75     1         0.007       2.694E-05  3.999         3.999         1        
============ ========= ============ ====== ========= =========== ========== ============= ============= =========

Computation times by source typology
------------------------------------
============ =========== ========== ============= ============= ========= ======
source_class filter_time split_time cum_calc_time max_calc_time num_tasks counts
============ =========== ========== ============= ============= ========= ======
PointSource  0.007       2.694E-05  3.999         3.999         1         1     
============ =========== ========== ============= ============= ========= ======

Information about the tasks
---------------------------
========================== ===== ====== ===== ===== =========
measurement                mean  stddev min   max   num_tasks
compute_ruptures.time_sec  4.000 NaN    4.000 4.000 1        
compute_ruptures.memory_mb 0.0   NaN    0.0   0.0   1        
========================== ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total compute_ruptures         4.000     0.0       1     
reading composite source model 0.016     0.0       1     
store source_info              0.015     0.0       1     
managing sources               0.013     0.0       1     
saving ruptures                0.011     0.0       1     
filtering sources              0.007     0.0       1     
aggregate curves               0.002     0.0       1     
filtering ruptures             0.002     0.0       6     
reading site collection        5.603E-05 0.0       1     
splitting sources              2.694E-05 0.0       1     
============================== ========= ========= ======