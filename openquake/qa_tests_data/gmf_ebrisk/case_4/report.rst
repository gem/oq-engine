event based two source models
=============================

============== ===================
checksum32     2,633,907,336      
date           2017-12-21T06:52:04
engine_version 2.9.0-git98c8442   
============== ===================

num_sites = 1, num_imts = 1

Parameters
----------
=============================== ==================
calculation_mode                'event_based'     
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              1.0               
ses_per_logic_tree_path         2                 
truncation_level                3.0               
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                0.1               
area_source_discretization      10.0              
ground_motion_correlation_model 'JB2009'          
random_seed                     24                
master_seed                     0                 
=============================== ==================

Input files
-----------
======================== ==========================================================================
Name                     File                                                                      
======================== ==========================================================================
exposure                 `exposure_model.xml <exposure_model.xml>`_                                
gsim_logic_tree          `gsim_logic_tree.xml <gsim_logic_tree.xml>`_                              
job_ini                  `job_haz.ini <job_haz.ini>`_                                              
source                   `source_model_1.xml <source_model_1.xml>`_                                
source                   `source_model_2.xml <source_model_2.xml>`_                                
source_model_logic_tree  `source_model_logic_tree.xml <source_model_logic_tree.xml>`_              
structural_vulnerability `structural_vulnerability_model.xml <structural_vulnerability_model.xml>`_
======================== ==========================================================================

Composite source model
----------------------
========= ====== =============== ================
smlt_path weight gsim_logic_tree num_realizations
========= ====== =============== ================
b1        0.250  trivial(1,1)    1/1             
b2        0.750  trivial(1,1)    1/1             
========= ====== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== =================== ========= ========== ==========
grp_id gsims               distances siteparams ruptparams
====== =================== ========= ========== ==========
0      BooreAtkinson2008() rjb       vs30       mag rake  
1      AkkarBommer2010()   rjb       vs30       mag rake  
2      BooreAtkinson2008() rjb       vs30       mag rake  
3      AkkarBommer2010()   rjb       vs30       mag rake  
====== =================== ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=4, rlzs=2)
  0,BooreAtkinson2008(): [0]
  1,AkkarBommer2010(): [0]
  2,BooreAtkinson2008(): [1]
  3,AkkarBommer2010(): [1]>

Number of ruptures per tectonic region type
-------------------------------------------
================== ====== ==================== ============ ============
source_model       grp_id trt                  eff_ruptures tot_ruptures
================== ====== ==================== ============ ============
source_model_1.xml 0      Active Shallow Crust 482          482         
source_model_1.xml 1      Stable Shallow Crust 4            4           
source_model_2.xml 2      Active Shallow Crust 482          482         
source_model_2.xml 3      Stable Shallow Crust 1            1           
================== ====== ==================== ============ ============

============= ===
#TRT models   4  
#eff_ruptures 969
#tot_ruptures 969
#tot_weight   0  
============= ===

Informational data
------------------
============================ =================================================================================
compute_ruptures.received    tot 10.43 KB, max_per_task 3.07 KB                                               
compute_ruptures.sent        sources 27.88 KB, src_filter 5.34 KB, param 5.04 KB, monitor 2.52 KB, gsims 808 B
hazard.input_weight          969.0                                                                            
hazard.n_imts                1                                                                                
hazard.n_levels              11                                                                               
hazard.n_realizations        2                                                                                
hazard.n_sites               1                                                                                
hazard.n_sources             4                                                                                
hazard.output_weight         0.08                                                                             
hostname                     tstation.gem.lan                                                                 
require_epsilons             True                                                                             
============================ =================================================================================

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
tax1     1.000 NaN    1   1   1         1         
======== ===== ====== === === ========= ==========

Slowest sources
---------------
========= ========================= ============ ========= ========= =========
source_id source_class              num_ruptures calc_time num_sites num_split
========= ========================= ============ ========= ========= =========
1         SimpleFaultSource         482          0.0       1         0        
2         CharacteristicFaultSource 1            0.0       1         0        
========= ========================= ============ ========= ========= =========

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
compute_ruptures   0.047 0.028  0.004 0.074 8        
================== ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total compute_ruptures         0.378     4.699     8     
managing sources               0.223     0.0       1     
reading composite source model 0.025     0.0       1     
saving ruptures                0.008     0.0       8     
reading exposure               0.008     0.0       1     
store source_info              0.005     0.0       1     
making contexts                0.003     0.0       2     
setting event years            0.002     0.0       1     
reading site collection        6.437E-06 0.0       1     
============================== ========= ========= ======