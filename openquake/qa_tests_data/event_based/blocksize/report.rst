QA test for blocksize independence (hazard)
===========================================

gem-tstation:/home/michele/ssd/calc_43344.hdf5 updated Wed Aug 24 20:19:05 2016

num_sites = 2, sitecol = 785 B

Parameters
----------
============================ ================================
calculation_mode             'event_based'                   
number_of_logic_tree_samples 1                               
maximum_distance             {u'Active Shallow Crust': 400.0}
investigation_time           5.0                             
ses_per_logic_tree_path      1                               
truncation_level             3.0                             
rupture_mesh_spacing         10.0                            
complex_fault_mesh_spacing   10.0                            
width_of_mfd_bin             0.5                             
area_source_discretization   10.0                            
random_seed                  1024                            
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
====== ================= =========== ======================= =================
grp_id gsims             distances   siteparams              ruptparams       
====== ================= =========== ======================= =================
0      ChiouYoungs2008() rx rjb rrup vs30measured vs30 z1pt0 rake dip ztor mag
====== ================= =========== ======================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)
  0,ChiouYoungs2008(): ['<0,b1~b1,w=1.0>']>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== =========== ============ ======
source_model     grp_id trt                  num_sources eff_ruptures weight
================ ====== ==================== =========== ============ ======
source_model.xml 0      Active Shallow Crust 3           3            277   
================ ====== ==================== =========== ============ ======

Informational data
------------------
====================================== ============
compute_ruptures_max_received_per_task 7,395       
compute_ruptures_num_tasks             10          
compute_ruptures_sent.monitor          8,680       
compute_ruptures_sent.rlzs_by_gsim     5,230       
compute_ruptures_sent.sitecol          4,530       
compute_ruptures_sent.sources          528,702     
compute_ruptures_tot_received          46,753      
hazard.input_weight                    560         
hazard.n_imts                          1           
hazard.n_levels                        4.000       
hazard.n_realizations                  1           
hazard.n_sites                         2           
hazard.n_sources                       9           
hazard.output_weight                   0.100       
hostname                               gem-tstation
====================================== ============

Specific information for event based
------------------------------------
======================== =====
Total number of ruptures 3    
Total number of events   3    
Rupture multiplicity     1.000
======================== =====

Slowest sources
---------------
============ ========= ============ ====== ========= =========== ========== ============= ============= =========
src_group_id source_id source_class weight split_num filter_time split_time cum_calc_time max_calc_time num_tasks
============ ========= ============ ====== ========= =========== ========== ============= ============= =========
0            1         AreaSource   175    1,170     7.951E-04   0.271      2.431         0.004         1,170    
0            2         AreaSource   58     389       7.050E-04   0.087      0.765         0.006         389      
0            3         AreaSource   44     352       7.110E-04   0.070      0.367         0.005         209      
============ ========= ============ ====== ========= =========== ========== ============= ============= =========

Computation times by source typology
------------------------------------
============ =========== ========== ============= ============= ========= ======
source_class filter_time split_time cum_calc_time max_calc_time num_tasks counts
============ =========== ========== ============= ============= ========= ======
AreaSource   0.002       0.429      3.562         0.015         1,768     3     
============ =========== ========== ============= ============= ========= ======

Information about the tasks
---------------------------
========================== ===== ====== ===== ===== =========
measurement                mean  stddev min   max   num_tasks
compute_ruptures.time_sec  0.358 0.081  0.178 0.414 10       
compute_ruptures.memory_mb 0.0   0.0    0.0   0.0   10       
========================== ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total compute_ruptures         3.581     0.0       10    
reading composite source model 1.522     0.0       1     
managing sources               0.520     0.0       1     
splitting sources              0.429     0.0       3     
store source_info              0.026     0.0       1     
filtering sources              0.007     0.0       9     
saving ruptures                0.003     0.0       1     
aggregate curves               0.002     0.0       10    
filtering ruptures             8.259E-04 0.0       3     
reading site collection        3.386E-05 0.0       1     
============================== ========= ========= ======