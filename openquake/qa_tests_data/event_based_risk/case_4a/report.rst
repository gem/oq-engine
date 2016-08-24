Event Based Hazard
==================

gem-tstation:/home/michele/ssd/calc_41988.hdf5 updated Wed Aug 24 08:03:11 2016

num_sites = 1, sitecol = 739 B

Parameters
----------
============================ ================================
calculation_mode             'event_based'                   
number_of_logic_tree_samples 0                               
maximum_distance             {u'Active Shallow Crust': 200.0}
investigation_time           1.0                             
ses_per_logic_tree_path      100                             
truncation_level             3.0                             
rupture_mesh_spacing         2.0                             
complex_fault_mesh_spacing   2.0                             
width_of_mfd_bin             0.1                             
area_source_discretization   10.0                            
random_seed                  24                              
master_seed                  0                               
engine_version               '2.1.0-git46eb8e0'              
============================ ================================

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
source_model.xml 0      Active Shallow Crust 2           5            483   
================ ====== ==================== =========== ============ ======

Informational data
------------------
====================================== ============
compute_ruptures_max_received_per_task 12,562      
compute_ruptures_num_tasks             14          
compute_ruptures_sent.monitor          12,922      
compute_ruptures_sent.rlzs_by_gsim     7,210       
compute_ruptures_sent.sitecol          8,456       
compute_ruptures_sent.sources          30,006      
compute_ruptures_tot_received          42,081      
hazard.input_weight                    483         
hazard.n_imts                          1           
hazard.n_levels                        11          
hazard.n_realizations                  1           
hazard.n_sites                         1           
hazard.n_sources                       2           
hazard.output_weight                   1.000       
hostname                               gem-tstation
require_epsilons                       1           
====================================== ============

Specific information for event based
------------------------------------
======================== =====
Total number of ruptures 5    
Total number of events   6    
Rupture multiplicity     1.200
======================== =====

Exposure model
--------------
=============== ========
#assets         1       
#taxonomies     1       
deductibile     absolute
insurance_limit absolute
=============== ========

======== ===== ====== === === ========= ==========
taxonomy mean  stddev min max num_sites num_assets
Wood     1.000 NaN    1   1   1         1         
======== ===== ====== === === ========= ==========

Slowest sources
---------------
============ ========= ========================= ====== ========= =========== ========== ============= ============= =========
src_group_id source_id source_class              weight split_num filter_time split_time cum_calc_time max_calc_time num_tasks
============ ========= ========================= ====== ========= =========== ========== ============= ============= =========
0            3         SimpleFaultSource         482    15        0.002       0.035      0.264         0.034         15       
0            1         CharacteristicFaultSource 1.000  1         0.002       0.0        0.022         0.022         1        
============ ========= ========================= ====== ========= =========== ========== ============= ============= =========

Computation times by source typology
------------------------------------
========================= =========== ========== ============= ============= ========= ======
source_class              filter_time split_time cum_calc_time max_calc_time num_tasks counts
========================= =========== ========== ============= ============= ========= ======
CharacteristicFaultSource 0.002       0.0        0.022         0.022         1         1     
SimpleFaultSource         0.002       0.035      0.264         0.034         15        1     
========================= =========== ========== ============= ============= ========= ======

Information about the tasks
---------------------------
========================== ===== ====== ===== ===== =========
measurement                mean  stddev min   max   num_tasks
compute_ruptures.time_sec  0.021 0.008  0.008 0.034 14       
compute_ruptures.memory_mb 0.002 0.007  0.0   0.027 14       
========================== ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total compute_ruptures         0.292     0.027     14    
managing sources               0.071     0.0       1     
splitting sources              0.035     0.0       1     
filtering ruptures             0.034     0.0       5     
reading composite source model 0.015     0.0       1     
store source_info              0.006     0.0       1     
saving ruptures                0.004     0.0       1     
filtering sources              0.004     0.0       2     
reading exposure               0.003     0.0       1     
aggregate curves               0.003     0.0       14    
reading site collection        9.060E-06 0.0       1     
============================== ========= ========= ======