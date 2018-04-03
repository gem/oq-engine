Event Based Hazard
==================

============== ===================
checksum32     117,701,076        
date           2018-03-26T15:55:09
engine_version 2.10.0-git543cfb0  
============== ===================

num_sites = 1, num_levels = 11

Parameters
----------
=============================== ==================
calculation_mode                'event_based'     
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              1.0               
ses_per_logic_tree_path         100               
truncation_level                3.0               
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                0.1               
area_source_discretization      10.0              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     24                
master_seed                     0                 
ses_seed                        42                
=============================== ==================

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
========= ====== =============== ================
smlt_path weight gsim_logic_tree num_realizations
========= ====== =============== ================
b1        1.000  trivial(1)      1/1             
========= ====== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================ ========= ========== ==========
grp_id gsims            distances siteparams ruptparams
====== ================ ========= ========== ==========
0      SadighEtAl1997() rrup      vs30       mag rake  
====== ================ ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)
  0,SadighEtAl1997(): [0]>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== ============ ============
source_model     grp_id trt                  eff_ruptures tot_ruptures
================ ====== ==================== ============ ============
source_model.xml 0      Active Shallow Crust 483          483         
================ ====== ==================== ============ ============

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
========= ========================= ============ ========= ========== ========= =========
source_id source_class              num_ruptures calc_time split_time num_sites num_split
========= ========================= ============ ========= ========== ========= =========
3         SimpleFaultSource         482          0.0       3.347E-04  0         0        
1         CharacteristicFaultSource 1            0.0       5.007E-06  0         0        
========= ========================= ============ ========= ========== ========= =========

Computation times by source typology
------------------------------------
========================= ========= ======
source_class              calc_time counts
========================= ========= ======
CharacteristicFaultSource 0.0       1     
SimpleFaultSource         0.0       1     
========================= ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
compute_ruptures   0.049 0.020  0.027 0.076 6        
================== ===== ====== ===== ===== =========

Informational data
------------------
================ ============================================================================= ========
task             sent                                                                          received
compute_ruptures sources=21.27 KB src_filter=4.23 KB param=3.78 KB monitor=1.93 KB gsims=720 B 10.2 KB 
================ ============================================================================= ========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total compute_ruptures         0.292     4.312     6     
managing sources               0.122     0.0       1     
reading composite source model 0.022     0.0       1     
making contexts                0.019     0.0       5     
saving ruptures                0.008     0.0       6     
reading exposure               0.007     0.0       1     
store source_info              0.004     0.0       1     
setting event years            0.002     0.0       1     
splitting sources              8.461E-04 0.0       1     
unpickling compute_ruptures    5.884E-04 0.0       6     
reading site collection        5.198E-05 0.0       1     
============================== ========= ========= ======