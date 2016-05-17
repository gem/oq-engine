Classical PSHA using Area Source
================================

gem-tstation:/home/michele/ssd/calc_16382.hdf5 updated Mon May 16 14:21:27 2016

num_sites = 6, sitecol = 969 B

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
width_of_mfd_bin             0.2                
area_source_discretization   5.0                
random_seed                  23                 
master_seed                  0                  
sites_per_tile               1                  
oqlite_version               '0.13.0-git16c052c'
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
b1        1.000  `source_model.xml <source_model.xml>`_ simple(2)       2/2             
========= ====== ====================================== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ===================================== =========== ======================= =================
trt_id gsims                                 distances   siteparams              ruptparams       
====== ===================================== =========== ======================= =================
0      BooreAtkinson2008() ChiouYoungs2008() rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
====== ===================================== =========== ======================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=2, rlzs=2)
  0,BooreAtkinson2008(): ['<0,b1,b1,w=0.6>']
  0,ChiouYoungs2008(): ['<1,b1,b2,w=0.4>']>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== =========== ============ ======
source_model     trt_id trt                  num_sources eff_ruptures weight
================ ====== ==================== =========== ============ ======
source_model.xml 0      Active Shallow Crust 1           1,640        41    
================ ====== ==================== =========== ============ ======

Informational data
------------------
======================================== ==============
count_eff_ruptures_max_received_per_task 3480          
count_eff_ruptures_num_tasks             24            
count_eff_ruptures_sent.monitor          77304         
count_eff_ruptures_sent.rlzs_assoc       62208         
count_eff_ruptures_sent.sitecol          10488         
count_eff_ruptures_sent.siteidx          120           
count_eff_ruptures_sent.sources          267348        
count_eff_ruptures_tot_received          83514         
hazard.input_weight                      41.0          
hazard.n_imts                            3             
hazard.n_levels                          19.0          
hazard.n_realizations                    2             
hazard.n_sites                           6             
hazard.n_sources                         0             
hazard.output_weight                     684.0         
hostname                                 'gem-tstation'
======================================== ==============

Slowest sources
---------------
============ ========= ============ ====== ========= =========== ========== =========
trt_model_id source_id source_class weight split_num filter_time split_time calc_time
============ ========= ============ ====== ========= =========== ========== =========
0            1         AreaSource   41     205       0.009       0.038      0.0      
============ ========= ============ ====== ========= =========== ========== =========

Computation times by source typology
------------------------------------
============ =========== ========== ========= ======
source_class filter_time split_time calc_time counts
============ =========== ========== ========= ======
AreaSource   0.009       0.038      0.0       1     
============ =========== ========== ========= ======

Information about the tasks
---------------------------
Not available

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
managing sources               0.128     0.0       1     
reading composite source model 0.042     0.0       1     
splitting sources              0.038     0.0       1     
filtering sources              0.009     0.0       6     
total count_eff_ruptures       0.008     0.0       24    
store source_info              0.005     0.0       1     
reading site collection        0.002     0.0       1     
aggregate curves               4.132E-04 0.0       24    
============================== ========= ========= ======