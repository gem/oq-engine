Event Based Hazard
==================

=============================================== ========================
tstation.gem.lan:/mnt/ssd/oqdata/calc_7586.hdf5 Wed Apr 26 15:54:33 2017
engine_version                                  2.4.0-git9336bd0        
hazardlib_version                               0.24.0-gita895d4c       
=============================================== ========================

num_sites = 1, sitecol = 809 B

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
============================ ===============================================================================
compute_ruptures.received    tot 12.88 KB, max_per_task 5.77 KB                                             
compute_ruptures.sent        sources 18.62 KB, monitor 3.57 KB, src_filter 3.41 KB, gsims 364 B, param 260 B
hazard.input_weight          483                                                                            
hazard.n_imts                1 B                                                                            
hazard.n_levels              11 B                                                                           
hazard.n_realizations        1 B                                                                            
hazard.n_sites               1 B                                                                            
hazard.n_sources             2 B                                                                            
hazard.output_weight         1.000                                                                          
hostname                     tstation.gem.lan                                                               
require_epsilons             1 B                                                                            
============================ ===============================================================================

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
0      3         SimpleFaultSource         482          0.0       1         0        
0      1         CharacteristicFaultSource 1            0.0       1         0        
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
compute_ruptures   0.061 0.039  0.004 0.094 4        
================== ===== ====== ===== ===== =========

Slowest operations
------------------
================================ ========= ========= ======
operation                        time_sec  memory_mb counts
================================ ========= ========= ======
total compute_ruptures           0.243     0.0       4     
saving ruptures                  0.012     0.0       4     
reading composite source model   0.011     0.0       1     
building site collection         0.005     0.0       1     
filtering composite source model 0.003     0.0       1     
setting event years              0.002     0.0       1     
filtering ruptures               0.001     0.0       5     
reading exposure                 0.001     0.0       1     
store source_info                8.938E-04 0.0       1     
managing sources                 1.013E-04 0.0       1     
reading site collection          8.345E-06 0.0       1     
================================ ========= ========= ======