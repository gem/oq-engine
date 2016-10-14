Event Based Hazard
==================

============================================== ========================
gem-tstation:/home/michele/ssd/calc_60079.hdf5 Tue Oct 11 06:56:16 2016
engine_version                                 2.1.0-git4e31fdd        
hazardlib_version                              0.21.0-gitab31f47       
============================================== ========================

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
================ ====== ==================== =========== ============ ============
source_model     grp_id trt                  num_sources eff_ruptures tot_ruptures
================ ====== ==================== =========== ============ ============
source_model.xml 0      Active Shallow Crust 2           5            483         
================ ====== ==================== =========== ============ ============

Informational data
------------------
====================================== ============
compute_ruptures_max_received_per_task 12,565      
compute_ruptures_num_tasks             4           
compute_ruptures_sent.gsims            328         
compute_ruptures_sent.monitor          4,320       
compute_ruptures_sent.sitecol          2,743       
compute_ruptures_sent.sources          19,824      
compute_ruptures_tot_received          23,985      
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
Total number of events   1    
Rupture multiplicity     0.200
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
====== ========= ========================= ============ ========= ========= =========
grp_id source_id source_class              num_ruptures calc_time num_sites num_split
====== ========= ========================= ============ ========= ========= =========
0      1         CharacteristicFaultSource 1            0.0       1         0        
0      3         SimpleFaultSource         482          0.0       1         0        
====== ========= ========================= ============ ========= ========= =========

Computation times by source typology
------------------------------------
========================= ========= ======
source_class              calc_time counts
========================= ========= ======
CharacteristicFaultSource 0.0       1     
SimpleFaultSource         0.0       1     
========================= ========= ======

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
compute_ruptures   0.066 0.032  0.022 0.097 4        
================== ===== ====== ===== ===== =========

Slowest operations
------------------
================================ ========= ========= ======
operation                        time_sec  memory_mb counts
================================ ========= ========= ======
total compute_ruptures           0.265     1.316     4     
managing sources                 0.068     0.0       1     
split/filter heavy sources       0.066     0.0       1     
filtering ruptures               0.032     0.0       5     
reading composite source model   0.018     0.0       1     
saving ruptures                  0.009     0.0       4     
filtering composite source model 0.004     0.0       1     
reading exposure                 0.003     0.0       1     
store source_info                8.180E-04 0.0       1     
Initializing rupture serials     3.290E-05 0.0       1     
reading site collection          7.153E-06 0.0       1     
================================ ========= ========= ======