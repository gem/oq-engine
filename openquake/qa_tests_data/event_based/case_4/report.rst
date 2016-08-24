Event-Based Hazard QA Test, Case 4
==================================

thinkpad:/home/michele/oqdata/calc_16911.hdf5 updated Wed Aug 24 04:48:51 2016

num_sites = 1, sitecol = 739 B

Parameters
----------
============================ ================================
calculation_mode             'event_based'                   
number_of_logic_tree_samples 0                               
maximum_distance             {u'active shallow crust': 200.0}
investigation_time           1.0                             
ses_per_logic_tree_path      50                              
truncation_level             0.0                             
rupture_mesh_spacing         1.0                             
complex_fault_mesh_spacing   1.0                             
width_of_mfd_bin             1.0                             
area_source_discretization   10.0                            
random_seed                  1066                            
master_seed                  0                               
engine_version               '2.1.0-git74bd74a'              
============================ ================================

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
================ ====== ==================== =========== ============ ======
source_model     grp_id trt                  num_sources eff_ruptures weight
================ ====== ==================== =========== ============ ======
source_model.xml 0      Active Shallow Crust 1           10           10    
================ ====== ==================== =========== ============ ======

Informational data
------------------
====================================== ========
compute_ruptures_max_received_per_task 8,746   
compute_ruptures_num_tasks             1       
compute_ruptures_sent.monitor          812     
compute_ruptures_sent.rlzs_by_gsim     516     
compute_ruptures_sent.sitecol          433     
compute_ruptures_sent.sources          1,267   
compute_ruptures_tot_received          8,746   
hazard.input_weight                    10      
hazard.n_imts                          1       
hazard.n_levels                        3.000   
hazard.n_realizations                  1       
hazard.n_sites                         1       
hazard.n_sources                       1       
hazard.output_weight                   0.500   
hostname                               thinkpad
====================================== ========

Specific information for event based
------------------------------------
======================== =====
Total number of ruptures 10   
Total number of events   44   
Rupture multiplicity     4.400
======================== =====

Slowest sources
---------------
============ ========= ================= ====== ========= =========== ========== ============= ============= =========
src_group_id source_id source_class      weight split_num filter_time split_time cum_calc_time max_calc_time num_tasks
============ ========= ================= ====== ========= =========== ========== ============= ============= =========
0            1         SimpleFaultSource 10     1         0.002       0.002      0.017         0.017         1        
============ ========= ================= ====== ========= =========== ========== ============= ============= =========

Computation times by source typology
------------------------------------
================= =========== ========== ============= ============= ========= ======
source_class      filter_time split_time cum_calc_time max_calc_time num_tasks counts
================= =========== ========== ============= ============= ========= ======
SimpleFaultSource 0.002       0.002      0.017         0.017         1         1     
================= =========== ========== ============= ============= ========= ======

Information about the tasks
---------------------------
========================== ===== ====== ===== ===== =========
measurement                mean  stddev min   max   num_tasks
compute_ruptures.time_sec  0.018 NaN    0.018 0.018 1        
compute_ruptures.memory_mb 1.309 NaN    1.309 1.309 1        
========================== ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total compute_ruptures         0.018     1.309     1     
saving ruptures                0.015     0.0       1     
store source_info              0.012     0.0       1     
managing sources               0.009     0.0       1     
filtering ruptures             0.008     0.0       10    
reading composite source model 0.008     0.0       1     
splitting sources              0.002     0.0       1     
filtering sources              0.002     0.0       1     
aggregate curves               0.001     0.0       1     
reading site collection        3.982E-05 0.0       1     
============================== ========= ========= ======