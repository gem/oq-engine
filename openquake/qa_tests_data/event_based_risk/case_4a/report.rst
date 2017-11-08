Event Based Hazard
==================

============== ===================
checksum32     117,701,076        
date           2017-11-08T18:06:36
engine_version 2.8.0-gite3d0f56   
============== ===================

num_sites = 1, num_imts = 1

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
random_seed                     24                
master_seed                     0                 
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
================ ====== ==================== =========== ============ ============
source_model     grp_id trt                  num_sources eff_ruptures tot_ruptures
================ ====== ==================== =========== ============ ============
source_model.xml 0      Active Shallow Crust 2           483          483         
================ ====== ==================== =========== ============ ============

Informational data
------------------
========================= =================================================================================
compute_ruptures.received tot 11.01 KB, max_per_task 5.3 KB                                                
compute_ruptures.sent     sources 18.67 KB, src_filter 3.41 KB, param 2.56 KB, monitor 1.27 KB, gsims 364 B
hazard.input_weight       483.0                                                                            
hazard.n_imts             1                                                                                
hazard.n_levels           11                                                                               
hazard.n_realizations     1                                                                                
hazard.n_sites            1                                                                                
hazard.n_sources          2                                                                                
hazard.output_weight      1.0                                                                              
hostname                  tstation.gem.lan                                                                 
require_epsilons          True                                                                             
========================= =================================================================================

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

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
compute_ruptures   0.065 0.042  0.004 0.098 4        
================== ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total compute_ruptures         0.260     0.043     4     
managing sources               0.061     0.0       1     
saving ruptures                0.013     0.0       4     
reading composite source model 0.011     0.0       1     
reading exposure               0.008     0.0       1     
store source_info              0.006     0.0       1     
prefiltering source model      0.003     0.0       1     
setting event years            0.002     0.0       1     
filtering ruptures             0.001     0.0       5     
reading site collection        7.629E-06 0.0       1     
============================== ========= ========= ======