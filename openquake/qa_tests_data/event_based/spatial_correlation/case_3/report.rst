Probabilistic Event-Based QA Test with No Spatial Correlation, case 3
=====================================================================

gem-tstation:/home/michele/ssd/calc_43339.hdf5 updated Wed Aug 24 20:18:55 2016

num_sites = 2, sitecol = 785 B

Parameters
----------
============================ ================================
calculation_mode             'event_based'                   
number_of_logic_tree_samples 0                               
maximum_distance             {u'Active Shallow Crust': 200.0}
investigation_time           50.0                            
ses_per_logic_tree_path      300                             
truncation_level             None                            
rupture_mesh_spacing         2.0                             
complex_fault_mesh_spacing   2.0                             
width_of_mfd_bin             0.1                             
area_source_discretization   10.0                            
random_seed                  123456789                       
master_seed                  0                               
engine_version               '2.1.0-git50eb989'              
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
compute_ruptures_max_received_per_task 728,254     
compute_ruptures_num_tasks             1           
compute_ruptures_sent.monitor          801         
compute_ruptures_sent.rlzs_by_gsim     529         
compute_ruptures_sent.sitecol          453         
compute_ruptures_sent.sources          1,324       
compute_ruptures_tot_received          728,254     
hazard.input_weight                    0.025       
hazard.n_imts                          1           
hazard.n_levels                        1.000       
hazard.n_realizations                  1           
hazard.n_sites                         2           
hazard.n_sources                       1           
hazard.output_weight                   300         
hostname                               gem-tstation
====================================== ============

Specific information for event based
------------------------------------
======================== ======
Total number of ruptures 1     
Total number of events   45,319
Rupture multiplicity     45,319
======================== ======

Slowest sources
---------------
============ ========= ============ ====== ========= =========== ========== ============= ============= =========
src_group_id source_id source_class weight split_num filter_time split_time cum_calc_time max_calc_time num_tasks
============ ========= ============ ====== ========= =========== ========== ============= ============= =========
0            1         PointSource  0.025  1         3.290E-05   0.0        0.487         0.487         1        
============ ========= ============ ====== ========= =========== ========== ============= ============= =========

Computation times by source typology
------------------------------------
============ =========== ========== ============= ============= ========= ======
source_class filter_time split_time cum_calc_time max_calc_time num_tasks counts
============ =========== ========== ============= ============= ========= ======
PointSource  3.290E-05   0.0        0.487         0.487         1         1     
============ =========== ========== ============= ============= ========= ======

Information about the tasks
---------------------------
========================== ===== ====== ===== ===== =========
measurement                mean  stddev min   max   num_tasks
compute_ruptures.time_sec  0.487 NaN    0.487 0.487 1        
compute_ruptures.memory_mb 0.0   NaN    0.0   0.0   1        
========================== ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
saving ruptures                0.507     0.0       1     
total compute_ruptures         0.487     0.0       1     
store source_info              0.012     0.0       1     
reading composite source model 0.005     0.0       1     
managing sources               0.003     0.0       1     
aggregate curves               0.002     0.0       1     
filtering ruptures             5.150E-04 0.0       1     
reading site collection        4.196E-05 0.0       1     
filtering sources              3.290E-05 0.0       1     
============================== ========= ========= ======