Event Based QA Test, Case 12
============================

thinkpad:/home/michele/oqdata/calc_16908.hdf5 updated Wed Aug 24 04:48:48 2016

num_sites = 1, sitecol = 739 B

Parameters
----------
============================ ==============================================================
calculation_mode             'event_based'                                                 
number_of_logic_tree_samples 0                                                             
maximum_distance             {u'stable continental': 200.0, u'active shallow crust': 200.0}
investigation_time           1.0                                                           
ses_per_logic_tree_path      3500                                                          
truncation_level             2.0                                                           
rupture_mesh_spacing         1.0                                                           
complex_fault_mesh_spacing   1.0                                                           
width_of_mfd_bin             1.0                                                           
area_source_discretization   10.0                                                          
random_seed                  1066                                                          
master_seed                  0                                                             
engine_version               '2.1.0-git74bd74a'                                            
============================ ==============================================================

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
b1        1.000  `source_model.xml <source_model.xml>`_ trivial(1,1)    1/1             
========= ====== ====================================== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== =================== ========= ========== ==========
grp_id gsims               distances siteparams ruptparams
====== =================== ========= ========== ==========
0      SadighEtAl1997()    rrup      vs30       rake mag  
1      BooreAtkinson2008() rjb       vs30       rake mag  
====== =================== ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=2, rlzs=1)
  0,SadighEtAl1997(): ['<0,b1~b1_b2,w=1.0>']
  1,BooreAtkinson2008(): ['<0,b1~b1_b2,w=1.0>']>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== =========== ============ ======
source_model     grp_id trt                  num_sources eff_ruptures weight
================ ====== ==================== =========== ============ ======
source_model.xml 0      Active Shallow Crust 1           1            0.025 
source_model.xml 1      Stable Continental   1           1            0.025 
================ ====== ==================== =========== ============ ======

=============== =====
#TRT models     2    
#sources        2    
#eff_ruptures   2    
filtered_weight 0.050
=============== =====

Informational data
------------------
====================================== ========
compute_ruptures_max_received_per_task 59,812  
compute_ruptures_num_tasks             2       
compute_ruptures_sent.monitor          1,690   
compute_ruptures_sent.rlzs_by_gsim     1,206   
compute_ruptures_sent.sitecol          866     
compute_ruptures_sent.sources          2,656   
compute_ruptures_tot_received          116,966 
hazard.input_weight                    0.050   
hazard.n_imts                          1       
hazard.n_levels                        3.000   
hazard.n_realizations                  1       
hazard.n_sites                         1       
hazard.n_sources                       2       
hazard.output_weight                   35      
hostname                               thinkpad
====================================== ========

Specific information for event based
------------------------------------
======================== =====
Total number of ruptures 2    
Total number of events   6,906
Rupture multiplicity     3,453
======================== =====

Slowest sources
---------------
============ ========= ============ ====== ========= =========== ========== ============= ============= =========
src_group_id source_id source_class weight split_num filter_time split_time cum_calc_time max_calc_time num_tasks
============ ========= ============ ====== ========= =========== ========== ============= ============= =========
0            1         PointSource  0.025  1         3.409E-05   0.0        0.075         0.075         1        
1            2         PointSource  0.025  1         1.597E-05   0.0        0.069         0.069         1        
============ ========= ============ ====== ========= =========== ========== ============= ============= =========

Computation times by source typology
------------------------------------
============ =========== ========== ============= ============= ========= ======
source_class filter_time split_time cum_calc_time max_calc_time num_tasks counts
============ =========== ========== ============= ============= ========= ======
PointSource  5.007E-05   0.0        0.144         0.144         2         2     
============ =========== ========== ============= ============= ========= ======

Information about the tasks
---------------------------
========================== ===== ====== ===== ===== =========
measurement                mean  stddev min   max   num_tasks
compute_ruptures.time_sec  0.073 0.004  0.070 0.075 2        
compute_ruptures.memory_mb 0.0   0.0    0.0   0.0   2        
========================== ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total compute_ruptures         0.145     0.0       2     
saving ruptures                0.124     0.0       1     
store source_info              0.010     0.0       1     
reading composite source model 0.007     0.0       1     
managing sources               0.006     0.0       1     
aggregate curves               0.004     0.0       2     
filtering ruptures             7.739E-04 0.0       2     
filtering sources              5.007E-05 0.0       2     
reading site collection        3.815E-05 0.0       1     
============================== ========= ========= ======