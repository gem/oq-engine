Event Based Hazard QA Test, Case 17
===================================

gem-tstation:/home/michele/ssd/calc_41621.hdf5 updated Tue Aug 23 17:47:49 2016

num_sites = 1, sitecol = 739 B

Parameters
----------
============================ ================================
calculation_mode             'event_based'                   
number_of_logic_tree_samples 5                               
maximum_distance             {u'active shallow crust': 200.0}
investigation_time           1.0                             
ses_per_logic_tree_path      3                               
truncation_level             2.0                             
rupture_mesh_spacing         1.0                             
complex_fault_mesh_spacing   1.0                             
width_of_mfd_bin             1.0                             
area_source_discretization   10.0                            
random_seed                  106                             
master_seed                  0                               
engine_version               '2.1.0-git5b04a6e'              
============================ ================================

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
1      SadighEtAl1997() rrup      vs30       rake mag  
====== ================ ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=5)
  1,SadighEtAl1997(): ['<1,b2~b1,w=0.2>', '<2,b2~b1,w=0.2>', '<3,b2~b1,w=0.2>', '<4,b2~b1,w=0.2>']>

Number of ruptures per tectonic region type
-------------------------------------------
================== ====== ==================== =========== ============ ======
source_model       grp_id trt                  num_sources eff_ruptures weight
================== ====== ==================== =========== ============ ======
source_model_2.xml 1      Active Shallow Crust 1           3            0.175 
================== ====== ==================== =========== ============ ======

Informational data
------------------
====================================== ============
compute_ruptures_max_received_per_task 5,184       
compute_ruptures_num_tasks             2           
compute_ruptures_sent.monitor          1,718       
compute_ruptures_sent.rlzs_by_gsim     1,302       
compute_ruptures_sent.sitecol          866         
compute_ruptures_sent.sources          3,117       
compute_ruptures_tot_received          6,783       
hazard.input_weight                    1.675       
hazard.n_imts                          1           
hazard.n_levels                        3.000       
hazard.n_realizations                  5           
hazard.n_sites                         1           
hazard.n_sources                       2           
hazard.output_weight                   0.150       
hostname                               gem-tstation
====================================== ============

Specific information for event based
------------------------------------
======================== =====
Total number of ruptures 3    
Total number of events   23   
Rupture multiplicity     7.667
======================== =====

Slowest sources
---------------
============ ========= ============ ====== ========= =========== ========== ============= ============= =========
src_group_id source_id source_class weight split_num filter_time split_time cum_calc_time max_calc_time num_tasks
============ ========= ============ ====== ========= =========== ========== ============= ============= =========
0            1         PointSource  0.975  1         4.411E-05   0.0        0.024         0.024         1        
1            2         PointSource  0.175  1         1.597E-05   0.0        0.007         0.007         1        
============ ========= ============ ====== ========= =========== ========== ============= ============= =========

Computation times by source typology
------------------------------------
============ =========== ========== ============= ============= ========= ======
source_class filter_time split_time cum_calc_time max_calc_time num_tasks counts
============ =========== ========== ============= ============= ========= ======
PointSource  6.008E-05   0.0        0.032         0.032         2         2     
============ =========== ========== ============= ============= ========= ======

Information about the tasks
---------------------------
========================== ===== ====== ===== ===== =========
measurement                mean  stddev min   max   num_tasks
compute_ruptures.time_sec  0.016 0.012  0.008 0.025 2        
compute_ruptures.memory_mb 0.0   0.0    0.0   0.0   2        
========================== ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total compute_ruptures         0.033     0.0       2     
reading composite source model 0.007     0.0       1     
store source_info              0.007     0.0       1     
managing sources               0.005     0.0       1     
saving ruptures                0.004     0.0       1     
filtering ruptures             0.002     0.0       3     
aggregate curves               9.813E-04 0.0       2     
filtering sources              6.008E-05 0.0       2     
reading site collection        3.910E-05 0.0       1     
============================== ========= ========= ======