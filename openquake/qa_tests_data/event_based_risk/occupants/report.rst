event based risk
================

============== ===================
checksum32     852,550,231        
date           2017-12-06T11:19:29
engine_version 2.9.0-gite55e76e   
============== ===================

num_sites = 7, num_imts = 1

Parameters
----------
=============================== ==================
calculation_mode                'event_based_risk'
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              10000.0           
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                0.1               
area_source_discretization      None              
ground_motion_correlation_model 'JB2009'          
random_seed                     24                
master_seed                     42                
avg_losses                      True              
=============================== ==================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
exposure                `exposure_model.xml <exposure_model.xml>`_                  
gsim_logic_tree         `gsim_logic_tree.xml <gsim_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
occupants_vulnerability `vulnerability_model.xml <vulnerability_model.xml>`_        
source                  `source_model.xml <source_model.xml>`_                      
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ====== =============== ================
smlt_path weight gsim_logic_tree num_realizations
========= ====== =============== ================
b1        1.000  trivial(1)      1/1             
========= ====== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== =================== ========= ========== ==========
grp_id gsims               distances siteparams ruptparams
====== =================== ========= ========== ==========
0      BooreAtkinson2008() rjb       vs30       mag rake  
====== =================== ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)
  0,BooreAtkinson2008(): [0]>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== ============ ============
source_model     grp_id trt                  eff_ruptures tot_ruptures
================ ====== ==================== ============ ============
source_model.xml 0      Active Shallow Crust 482          482         
================ ====== ==================== ============ ============

Informational data
------------------
========================= ===================================================================================
compute_ruptures.received tot 252.58 KB, max_per_task 31.34 KB                                               
compute_ruptures.sent     sources 17.89 KB, src_filter 10.82 KB, param 7.15 KB, monitor 4.1 KB, gsims 1.29 KB
hazard.input_weight       482.0                                                                              
hazard.n_imts             1                                                                                  
hazard.n_levels           1                                                                                  
hazard.n_realizations     1                                                                                  
hazard.n_sites            7                                                                                  
hazard.n_sources          1                                                                                  
hazard.output_weight      7.0                                                                                
hostname                  tstation.gem.lan                                                                   
require_epsilons          True                                                                               
========================= ===================================================================================

Estimated data transfer for the avglosses
-----------------------------------------
7 asset(s) x 1 realization(s) x 1 loss type(s) x 1 losses x 8 bytes x 20 tasks = 1.09 KB

Exposure model
--------------
=============== ========
#assets         7       
#taxonomies     1       
deductibile     absolute
insurance_limit absolute
=============== ========

======== ===== ====== === === ========= ==========
taxonomy mean  stddev min max num_sites num_assets
tax1     1.000 0.0    1   1   7         7         
======== ===== ====== === === ========= ==========

Slowest sources
---------------
========= ================= ============ ========= ========= =========
source_id source_class      num_ruptures calc_time num_sites num_split
========= ================= ============ ========= ========= =========
1         SimpleFaultSource 482          0.0       1         0        
========= ================= ============ ========= ========= =========

Computation times by source typology
------------------------------------
================= ========= ======
source_class      calc_time counts
================= ========= ======
SimpleFaultSource 0.0       1     
================= ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
compute_ruptures   0.025 0.009  0.010 0.041 13       
================== ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total compute_ruptures         0.329     0.777     13    
managing sources               0.148     0.0       1     
filtering ruptures             0.118     0.0       259   
saving ruptures                0.029     0.0       13    
reading exposure               0.007     0.0       1     
reading composite source model 0.005     0.0       1     
store source_info              0.003     0.0       1     
setting event years            0.002     0.0       1     
reading site collection        6.199E-06 0.0       1     
============================== ========= ========= ======