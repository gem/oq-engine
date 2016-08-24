Probabilistic Event-Based QA Test with Spatial Correlation, case 2
==================================================================

gem-tstation:/home/michele/ssd/calc_42020.hdf5 updated Wed Aug 24 08:04:38 2016

num_sites = 2, sitecol = 785 B

Parameters
----------
============================ ================================
calculation_mode             'event_based'                   
number_of_logic_tree_samples 0                               
maximum_distance             {u'Active Shallow Crust': 200.0}
investigation_time           50.0                            
ses_per_logic_tree_path      150                             
truncation_level             None                            
rupture_mesh_spacing         2.0                             
complex_fault_mesh_spacing   2.0                             
width_of_mfd_bin             0.1                             
area_source_discretization   10.0                            
random_seed                  123456789                       
master_seed                  0                               
engine_version               '2.1.0-git46eb8e0'              
============================ ================================

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
====== =================== ========= ========== ==========
grp_id gsims               distances siteparams ruptparams
====== =================== ========= ========== ==========
0      BooreAtkinson2008() rjb       vs30       rake mag  
====== =================== ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)
  0,BooreAtkinson2008(): ['<0,b1~b1,w=1.0>']>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== =========== ============ ======
source_model     grp_id trt                  num_sources eff_ruptures weight
================ ====== ==================== =========== ============ ======
source_model.xml 0      Active Shallow Crust 1           1            0.025 
================ ====== ==================== =========== ============ ======

Informational data
------------------
====================================== ============
compute_ruptures_max_received_per_task 364,262     
compute_ruptures_num_tasks             1           
compute_ruptures_sent.monitor          800         
compute_ruptures_sent.rlzs_by_gsim     529         
compute_ruptures_sent.sitecol          453         
compute_ruptures_sent.sources          1,322       
compute_ruptures_tot_received          364,262     
hazard.input_weight                    0.025       
hazard.n_imts                          1           
hazard.n_levels                        1.000       
hazard.n_realizations                  1           
hazard.n_sites                         2           
hazard.n_sources                       1           
hazard.output_weight                   150         
hostname                               gem-tstation
====================================== ============

Specific information for event based
------------------------------------
======================== ======
Total number of ruptures 1     
Total number of events   22,566
Rupture multiplicity     22,566
======================== ======

Slowest sources
---------------
============ ========= ============ ====== ========= =========== ========== ============= ============= =========
src_group_id source_id source_class weight split_num filter_time split_time cum_calc_time max_calc_time num_tasks
============ ========= ============ ====== ========= =========== ========== ============= ============= =========
0            1         PointSource  0.025  1         2.480E-05   0.0        0.168         0.168         1        
============ ========= ============ ====== ========= =========== ========== ============= ============= =========

Computation times by source typology
------------------------------------
============ =========== ========== ============= ============= ========= ======
source_class filter_time split_time cum_calc_time max_calc_time num_tasks counts
============ =========== ========== ============= ============= ========= ======
PointSource  2.480E-05   0.0        0.168         0.168         1         1     
============ =========== ========== ============= ============= ========= ======

Information about the tasks
---------------------------
========================== ===== ====== ===== ===== =========
measurement                mean  stddev min   max   num_tasks
compute_ruptures.time_sec  0.168 NaN    0.168 0.168 1        
compute_ruptures.memory_mb 0.531 NaN    0.531 0.531 1        
========================== ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
saving ruptures                0.174     0.0       1     
total compute_ruptures         0.168     0.531     1     
store source_info              0.005     0.0       1     
reading composite source model 0.004     0.0       1     
managing sources               0.003     0.0       1     
aggregate curves               6.769E-04 0.0       1     
filtering ruptures             2.518E-04 0.0       1     
reading site collection        3.099E-05 0.0       1     
filtering sources              2.480E-05 0.0       1     
============================== ========= ========= ======