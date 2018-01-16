Event Based Risk Lisbon
=======================

============== ===================
checksum32     1,228,666,719      
date           2018-01-11T04:29:28
engine_version 2.9.0-git3c583c4   
============== ===================

num_sites = 1, num_imts = 1

Parameters
----------
=============================== ==================
calculation_mode                'event_based_risk'
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 400.0}
investigation_time              2.0               
ses_per_logic_tree_path         1                 
truncation_level                5.0               
rupture_mesh_spacing            4.0               
complex_fault_mesh_spacing      4.0               
width_of_mfd_bin                0.1               
area_source_discretization      10.0              
ground_motion_correlation_model None              
random_seed                     23                
master_seed                     42                
avg_losses                      True              
=============================== ==================

Input files
-----------
======================== ============================================================
Name                     File                                                        
======================== ============================================================
exposure                 `exposure_model_1asset.xml <exposure_model_1asset.xml>`_    
gsim_logic_tree          `gsim_logic_tree.xml <gsim_logic_tree.xml>`_                
job_ini                  `job.ini <job.ini>`_                                        
source                   `SA_RA_CATAL1_00.xml <SA_RA_CATAL1_00.xml>`_                
source                   `SA_RA_CATAL2_00.xml <SA_RA_CATAL2_00.xml>`_                
source_model_logic_tree  `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
structural_vulnerability `vulnerability_model2013.xml <vulnerability_model2013.xml>`_
======================== ============================================================

Composite source model
----------------------
========= ====== =============== ================
smlt_path weight gsim_logic_tree num_realizations
========= ====== =============== ================
b1        0.600  complex(2,2)    4/4             
b2        0.400  complex(2,2)    4/4             
========= ====== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ===================================== ========= ========== ==========
grp_id gsims                                 distances siteparams ruptparams
====== ===================================== ========= ========== ==========
0      AkkarBommer2010() AtkinsonBoore2006() rjb rrup  vs30       mag rake  
1      AkkarBommer2010() AtkinsonBoore2006() rjb rrup  vs30       mag rake  
2      AkkarBommer2010() AtkinsonBoore2006() rjb rrup  vs30       mag rake  
3      AkkarBommer2010() AtkinsonBoore2006() rjb rrup  vs30       mag rake  
====== ===================================== ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=8, rlzs=8)
  0,AkkarBommer2010(): [2 3]
  0,AtkinsonBoore2006(): [0 1]
  1,AkkarBommer2010(): [1 3]
  1,AtkinsonBoore2006(): [0 2]
  2,AkkarBommer2010(): [6 7]
  2,AtkinsonBoore2006(): [4 5]
  3,AkkarBommer2010(): [5 7]
  3,AtkinsonBoore2006(): [4 6]>

Number of ruptures per tectonic region type
-------------------------------------------
=================== ====== ==================== ============ ============
source_model        grp_id trt                  eff_ruptures tot_ruptures
=================== ====== ==================== ============ ============
SA_RA_CATAL1_00.xml 0      Active Shallow Crust 36,196       48,521      
SA_RA_CATAL1_00.xml 1      Stable Shallow Crust 21,381       21,381      
SA_RA_CATAL2_00.xml 2      Active Shallow Crust 36,196       48,521      
SA_RA_CATAL2_00.xml 3      Stable Shallow Crust 21,381       21,381      
=================== ====== ==================== ============ ============

============= =======
#TRT models   4      
#eff_ruptures 115,154
#tot_ruptures 139,804
#tot_weight   0      
============= =======

Informational data
------------------
========================= ===================================================================================
compute_ruptures.received tot 53.13 KB, max_per_task 6.66 KB                                                 
compute_ruptures.sent     sources 997 KB, param 15.63 KB, src_filter 12.69 KB, monitor 5.68 KB, gsims 3.15 KB
hazard.input_weight       13980.399999999998                                                                 
hazard.n_imts             1                                                                                  
hazard.n_levels           40                                                                                 
hazard.n_realizations     8                                                                                  
hazard.n_sites            1                                                                                  
hazard.n_sources          22                                                                                 
hazard.output_weight      40.0                                                                               
hostname                  tstation.gem.lan                                                                   
require_epsilons          False                                                                              
========================= ===================================================================================

Estimated data transfer for the avglosses
-----------------------------------------
1 asset(s) x 8 realization(s) x 1 loss type(s) x 1 losses x 8 bytes x 16 tasks = 1 KB

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
M1_2_PC  1.000 NaN    1   1   1         1         
======== ===== ====== === === ========= ==========

Slowest sources
---------------
========= ============ ============ ========= ========= =========
source_id source_class num_ruptures calc_time num_sites num_split
========= ============ ============ ========= ========= =========
1         AreaSource   4,163        0.0       1         0        
7         AreaSource   1,690        0.0       1         0        
8         AreaSource   1,440        0.0       1         0        
0         AreaSource   24,435       0.0       1         0        
2         AreaSource   19,923       0.0       1         0        
4         AreaSource   1,280        0.0       1         0        
5         AreaSource   2,349        0.0       1         0        
3         AreaSource   3,509        0.0       1         0        
9         AreaSource   2,508        0.0       1         0        
6         AreaSource   4,123        0.0       1         0        
10        AreaSource   4,482        0.0       1         0        
========= ============ ============ ========= ========= =========

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
AreaSource   0.0       11    
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
compute_ruptures   1.659 0.687  0.334 2.587 18       
================== ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total compute_ruptures         29        0.387     18    
managing sources               4.230     0.0       1     
reading composite source model 1.675     0.0       1     
saving ruptures                0.024     0.0       18    
store source_info              0.007     0.0       1     
making contexts                0.007     0.0       12    
reading exposure               0.005     0.0       1     
setting event years            0.002     0.0       1     
reading site collection        4.768E-06 0.0       1     
============================== ========= ========= ======