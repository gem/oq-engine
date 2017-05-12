event based risk
================

================================================ ========================
tstation.gem.lan:/mnt/ssd/oqdata/calc_21311.hdf5 Fri May 12 10:45:36 2017
engine_version                                   2.4.0-git59713b5        
hazardlib_version                                0.24.0-git0596dd3       
================================================ ========================

num_sites = 7, sitecol = 1.11 KB

Parameters
----------
=============================== ==================
calculation_mode                'event_based_risk'
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
avg_losses                      True              
=============================== ==================

Input files
-----------
=================================== ================================================================================
Name                                File                                                                            
=================================== ================================================================================
business_interruption_vulnerability `downtime_vulnerability_model.xml <downtime_vulnerability_model.xml>`_          
contents_vulnerability              `contents_vulnerability_model.xml <contents_vulnerability_model.xml>`_          
exposure                            `exposure_model.xml <exposure_model.xml>`_                                      
gsim_logic_tree                     `gsim_logic_tree.xml <gsim_logic_tree.xml>`_                                    
job_ini                             `job.ini <job.ini>`_                                                            
nonstructural_vulnerability         `nonstructural_vulnerability_model.xml <nonstructural_vulnerability_model.xml>`_
occupants_vulnerability             `occupants_vulnerability_model.xml <occupants_vulnerability_model.xml>`_        
source                              `source_model_1.xml <source_model_1.xml>`_                                      
source                              `source_model_2.xml <source_model_2.xml>`_                                      
source_model_logic_tree             `source_model_logic_tree.xml <source_model_logic_tree.xml>`_                    
structural_vulnerability            `structural_vulnerability_model.xml <structural_vulnerability_model.xml>`_      
=================================== ================================================================================

Composite source model
----------------------
========= ====== ========================================== =============== ================
smlt_path weight source_model_file                          gsim_logic_tree num_realizations
========= ====== ========================================== =============== ================
b1        0.250  `source_model_1.xml <source_model_1.xml>`_ complex(2,2)    2/2             
b2        0.750  `source_model_2.xml <source_model_2.xml>`_ complex(2,2)    2/2             
========= ====== ========================================== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ===================================== =========== ======================= =================
grp_id gsims                                 distances   siteparams              ruptparams       
====== ===================================== =========== ======================= =================
1      AkkarBommer2010() ChiouYoungs2008()   rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
2      BooreAtkinson2008() ChiouYoungs2008() rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
====== ===================================== =========== ======================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=4, rlzs=4)
  1,AkkarBommer2010(): ['<0,b1~@_b21,w=0.15>']
  1,ChiouYoungs2008(): ['<1,b1~@_b22,w=0.1>']
  2,BooreAtkinson2008(): ['<2,b2~b11_@,w=0.5625>']
  2,ChiouYoungs2008(): ['<3,b2~b12_@,w=0.1875>']>

Number of ruptures per tectonic region type
-------------------------------------------
================== ====== ==================== =========== ============ ============
source_model       grp_id trt                  num_sources eff_ruptures tot_ruptures
================== ====== ==================== =========== ============ ============
source_model_1.xml 1      Stable Shallow Crust 1           1            4           
source_model_2.xml 2      Active Shallow Crust 1           1            482         
================== ====== ==================== =========== ============ ============

============= ===
#TRT models   2  
#sources      2  
#eff_ruptures 2  
#tot_ruptures 486
#tot_weight   969
============= ===

Informational data
------------------
============================ ===============================================================================
compute_ruptures.received    tot 9.99 KB, max_per_task 3.32 KB                                              
compute_ruptures.sent        sources 18.21 KB, monitor 5.51 KB, src_filter 3.33 KB, gsims 708 B, param 260 B
hazard.input_weight          969                                                                            
hazard.n_imts                4 B                                                                            
hazard.n_levels              46 B                                                                           
hazard.n_realizations        8 B                                                                            
hazard.n_sites               7 B                                                                            
hazard.n_sources             4 B                                                                            
hazard.output_weight         1,288                                                                          
hostname                     tstation.gem.lan                                                               
require_epsilons             1 B                                                                            
============================ ===============================================================================

Estimated data transfer for the avglosses
-----------------------------------------
7 asset(s) x 4 realization(s) x 5 loss type(s) x 2 losses x 8 bytes x 50 tasks = 109.38 KB

Exposure model
--------------
=============== ========
#assets         7       
#taxonomies     3       
deductibile     absolute
insurance_limit absolute
=============== ========

======== ===== ====== === === ========= ==========
taxonomy mean  stddev min max num_sites num_assets
tax1     1.000 0.0    1   1   4         4         
tax2     1.000 0.0    1   1   2         2         
tax3     1.000 NaN    1   1   1         1         
*ALL*    1.000 0.0    1   1   7         7         
======== ===== ====== === === ========= ==========

Slowest sources
---------------
====== ========= ========================= ============ ========= ========= =========
grp_id source_id source_class              num_ruptures calc_time num_sites num_split
====== ========= ========================= ============ ========= ========= =========
1      2         SimpleFaultSource         4            0.0       0         0        
3      2         CharacteristicFaultSource 1            0.0       0         0        
2      1         SimpleFaultSource         482          0.0       0         0        
0      1         SimpleFaultSource         482          0.0       0         0        
====== ========= ========================= ============ ========= ========= =========

Computation times by source typology
------------------------------------
========================= ========= ======
source_class              calc_time counts
========================= ========= ======
CharacteristicFaultSource 0.0       1     
SimpleFaultSource         0.0       3     
========================= ========= ======

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
compute_ruptures   0.042 0.041  0.004 0.078 4        
================== ===== ====== ===== ===== =========

Slowest operations
------------------
================================ ========= ========= ======
operation                        time_sec  memory_mb counts
================================ ========= ========= ======
total compute_ruptures           0.168     0.125     4     
reading composite source model   0.017     0.0       1     
reading exposure                 0.009     0.0       1     
saving ruptures                  0.008     0.0       4     
setting event years              0.005     0.0       1     
managing sources                 0.004     0.0       1     
store source_info                0.001     0.0       1     
filtering ruptures               7.541E-04 0.0       2     
filtering composite source model 5.794E-05 0.0       1     
reading site collection          8.583E-06 0.0       1     
================================ ========= ========= ======