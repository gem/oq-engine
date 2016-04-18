Event Based Hazard
==================

num_sites = 1, sitecol = 739 B

Parameters
----------
============================ ==================
calculation_mode             'event_based'     
number_of_logic_tree_samples 0                 
maximum_distance             {'default': 200.0}
investigation_time           1.0               
ses_per_logic_tree_path      100               
truncation_level             3.0               
rupture_mesh_spacing         2.0               
complex_fault_mesh_spacing   2.0               
width_of_mfd_bin             0.1               
area_source_discretization   10.0              
random_seed                  24                
master_seed                  0                 
concurrent_tasks             40                
============================ ==================

Input files
-----------
======================== ==========================================================================
Name                     File                                                                      
======================== ==========================================================================
exposure                 `exposure_model.xml <exposure_model.xml>`_                                
gsim_logic_tree          `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                              
job_ini                  `job_hazard.ini <job_hazard.ini>`_                                        
site_model               `site_model.xml <site_model.xml>`_                                        
source                   `source_model.xml <source_model.xml>`_                                    
source_model_logic_tree  `source_model_logic_tree.xml <source_model_logic_tree.xml>`_              
structural_vulnerability `structural_vulnerability_model.xml <structural_vulnerability_model.xml>`_
======================== ==========================================================================

Composite source model
----------------------
========= ====== ====================================== =============== ================
smlt_path weight source_model_file                      gsim_logic_tree num_realizations
========= ====== ====================================== =============== ================
b1        1.000  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
========= ====== ====================================== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ============== ========= ========== ==========
trt_id gsims          distances siteparams ruptparams
====== ============== ========= ========== ==========
0      SadighEtAl1997 rrup      vs30       rake mag  
====== ============== ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)
  0,SadighEtAl1997: ['<0,b1,b1,w=1.0>']>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== =========== ============ ======
source_model     trt_id trt                  num_sources eff_ruptures weight
================ ====== ==================== =========== ============ ======
source_model.xml 0      Active Shallow Crust 2           5            483   
================ ====== ==================== =========== ============ ======

Informational data
------------------
====================================== =====
compute_ruptures_max_received_per_task 13920
compute_ruptures_sent.Monitor          39232
compute_ruptures_sent.RlzsAssoc        46048
compute_ruptures_sent.SiteCollection   9664 
compute_ruptures_sent.WeightedSequence 31125
compute_ruptures_sent.int              80   
compute_ruptures_tot_received          68391
hazard.input_weight                    483.0
hazard.n_imts                          1    
hazard.n_levels                        11.0 
hazard.n_realizations                  1    
hazard.n_sites                         1    
hazard.n_sources                       0    
hazard.output_weight                   1.0  
====================================== =====

Exposure model
--------------
=========== =
#assets     1
#taxonomies 1
=========== =

======== =======
Taxonomy #Assets
======== =======
Wood     1      
======== =======

Slowest sources
---------------
============ ========= ==================== ====== ========= =========== ========== =========
trt_model_id source_id source_class         weight split_num filter_time split_time calc_time
============ ========= ==================== ====== ========= =========== ========== =========
0            3         SimpleFaultSource    482    15        0.002       0.042      0.365    
0            1         CharacteristicFaultS 1.000  1         0.002       0.0        0.027    
============ ========= ==================== ====== ========= =========== ========== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total compute_ruptures         0.399     0.0       16    
managing sources               0.074     0.0       1     
filtering ruptures             0.044     0.0       5     
splitting sources              0.042     0.0       1     
total compute_gmfs_and_curves  0.036     0.004     5     
make contexts                  0.031     0.0       5     
reading composite source model 0.018     0.0       1     
store source_info              0.004     0.0       1     
saving gmfs                    0.004     0.0       5     
filtering sources              0.004     0.0       2     
reading exposure               0.003     0.0       1     
saving ruptures                0.002     0.0       1     
compute poes                   0.002     0.0       5     
aggregate curves               0.002     0.0       16    
reading site collection        7.868E-06 0.0       1     
============================== ========= ========= ======