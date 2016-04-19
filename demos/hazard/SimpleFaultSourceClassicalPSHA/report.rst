Classical PSHA with Simple Fault Source
=======================================

Datastore /home/michele/ssd/calc_10531.hdf5 last updated Tue Apr 19 05:57:13 2016 on gem-tstation

num_sites = 1369, sitecol = 62.21 KB

Parameters
----------
============================ ===================
calculation_mode             'classical'        
number_of_logic_tree_samples 0                  
maximum_distance             {'default': 200.0} 
investigation_time           50.0               
ses_per_logic_tree_path      1                  
truncation_level             3.0                
rupture_mesh_spacing         2.0                
complex_fault_mesh_spacing   2.0                
width_of_mfd_bin             0.1                
area_source_discretization   5.0                
random_seed                  23                 
master_seed                  0                  
sites_per_tile               1000               
oqlite_version               '0.13.0-git7c9cf8e'
============================ ===================

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
====== ================= ========= ========== ==========
trt_id gsims             distances siteparams ruptparams
====== ================= ========= ========== ==========
0      BooreAtkinson2008 rjb       vs30       rake mag  
====== ================= ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)
  0,BooreAtkinson2008: ['<0,b1,b1,w=1.0>']>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== =========== ============ ======
source_model     trt_id trt                  num_sources eff_ruptures weight
================ ====== ==================== =========== ============ ======
source_model.xml 0      Active Shallow Crust 1           548          548   
================ ====== ==================== =========== ============ ======

Informational data
------------------
======================================== =================
count_eff_ruptures_max_received_per_task 3783             
count_eff_ruptures_num_tasks             79               
count_eff_ruptures_sent.monitor          281951           
count_eff_ruptures_sent.rlzs_assoc       226493           
count_eff_ruptures_sent.sitecol          2629278          
count_eff_ruptures_sent.siteidx          395              
count_eff_ruptures_sent.sources          1820426          
count_eff_ruptures_tot_received          298857           
hazard.input_weight                      548.0            
hazard.n_imts                            9                
hazard.n_levels                          21.88888888888889
hazard.n_realizations                    1                
hazard.n_sites                           1369             
hazard.n_sources                         0                
hazard.output_weight                     269693.0         
hostname                                 'gem-tstation'   
======================================== =================

Slowest sources
---------------
============ ========= ================= ====== ========= =========== ========== =========
trt_model_id source_id source_class      weight split_num filter_time split_time calc_time
============ ========= ================= ====== ========= =========== ========== =========
0            3         SimpleFaultSource 548    548       0.003       0.111      0.0      
============ ========= ================= ====== ========= =========== ========== =========

Slowest operations
------------------
============================== ======== ========= ======
operation                      time_sec memory_mb counts
============================== ======== ========= ======
managing sources               0.235    0.0       1     
reading site collection        0.163    0.0       1     
splitting sources              0.111    0.0       1     
total count_eff_ruptures       0.025    0.0       79    
reading composite source model 0.013    0.0       1     
store source_info              0.004    0.0       1     
filtering sources              0.003    0.0       1     
aggregate curves               0.001    0.0       79    
============================== ======== ========= ======