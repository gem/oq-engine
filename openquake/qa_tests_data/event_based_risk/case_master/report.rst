event based risk
================

============================================== ========================
gem-tstation:/home/michele/ssd/calc_66971.hdf5 Wed Nov  9 08:14:33 2016
engine_version                                 2.2.0-git54d01f4        
hazardlib_version                              0.22.0-git173c60c       
============================================== ========================

num_sites = 7, sitecol = 1015 B

Parameters
----------
============================ ================================================================
calculation_mode             'event_based_risk'                                              
number_of_logic_tree_samples 0                                                               
maximum_distance             {u'Stable Shallow Crust': 200.0, u'Active Shallow Crust': 200.0}
investigation_time           50.0                                                            
ses_per_logic_tree_path      2                                                               
truncation_level             3.0                                                             
rupture_mesh_spacing         2.0                                                             
complex_fault_mesh_spacing   2.0                                                             
width_of_mfd_bin             0.1                                                             
area_source_discretization   10.0                                                            
random_seed                  24                                                              
master_seed                  0                                                               
avg_losses                   True                                                            
============================ ================================================================

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
b1        0.250  `source_model_1.xml <source_model_1.xml>`_ complex(2,2)    4/4             
b2        0.750  `source_model_2.xml <source_model_2.xml>`_ complex(2,2)    2/2             
========= ====== ========================================== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ===================================== =========== ======================= =================
grp_id gsims                                 distances   siteparams              ruptparams       
====== ===================================== =========== ======================= =================
0      BooreAtkinson2008() ChiouYoungs2008() rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
1      AkkarBommer2010() ChiouYoungs2008()   rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
2      BooreAtkinson2008() ChiouYoungs2008() rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
====== ===================================== =========== ======================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=6, rlzs=6)
  0,BooreAtkinson2008(): ['<0,b1~b11_b21,w=0.1125>', '<1,b1~b11_b22,w=0.075>']
  0,ChiouYoungs2008(): ['<2,b1~b12_b21,w=0.0375>', '<3,b1~b12_b22,w=0.025>']
  1,AkkarBommer2010(): ['<0,b1~b11_b21,w=0.1125>', '<2,b1~b12_b21,w=0.0375>']
  1,ChiouYoungs2008(): ['<1,b1~b11_b22,w=0.075>', '<3,b1~b12_b22,w=0.025>']
  2,BooreAtkinson2008(): ['<4,b2~b11_@,w=0.5625>']
  2,ChiouYoungs2008(): ['<5,b2~b12_@,w=0.1875>']>

Number of ruptures per tectonic region type
-------------------------------------------
================== ====== ==================== =========== ============ ============
source_model       grp_id trt                  num_sources eff_ruptures tot_ruptures
================== ====== ==================== =========== ============ ============
source_model_1.xml 0      Active Shallow Crust 1           1            482         
source_model_1.xml 1      Stable Shallow Crust 1           4            4           
source_model_2.xml 2      Active Shallow Crust 1           4            482         
================== ====== ==================== =========== ============ ============

============= ===
#TRT models   3  
#sources      3  
#eff_ruptures 9  
#tot_ruptures 968
#tot_weight   969
============= ===

Informational data
------------------
============================================= ============
compute_gmfs_and_curves_max_received_per_task 67,413      
compute_gmfs_and_curves_num_tasks             9           
compute_gmfs_and_curves_sent.getter           40,291      
compute_gmfs_and_curves_sent.monitor          52,182      
compute_gmfs_and_curves_sent.rlzs             7,219       
compute_gmfs_and_curves_tot_received          330,515     
compute_ruptures_max_received_per_task        8,025       
compute_ruptures_num_tasks                    8           
compute_ruptures_sent.gsims                   1,336       
compute_ruptures_sent.monitor                 12,840      
compute_ruptures_sent.sitecol                 5,576       
compute_ruptures_sent.sources                 28,849      
compute_ruptures_tot_received                 33,848      
hazard.input_weight                           969         
hazard.n_imts                                 4           
hazard.n_levels                               46          
hazard.n_realizations                         8           
hazard.n_sites                                7           
hazard.n_sources                              4           
hazard.output_weight                          2,576       
hostname                                      gem-tstation
require_epsilons                              1           
============================================= ============

Specific information for event based
------------------------------------
======================== ===
Total number of ruptures 9  
Total number of events   106
Rupture multiplicity     11 
======================== ===

Estimated data transfer for the avglosses
-----------------------------------------
7 asset(s) x 6 realization(s) x 5 loss type(s) x 2 losses x 8 bytes x 50 tasks = 164.06 KB

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
1      2         SimpleFaultSource         4            0.0       7         0        
0      1         SimpleFaultSource         482          0.0       7         0        
3      2         CharacteristicFaultSource 1            0.0       7         0        
2      1         SimpleFaultSource         482          0.0       7         0        
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
compute_ruptures   0.038 0.020  0.004 0.057 8        
================== ===== ====== ===== ===== =========

Slowest operations
------------------
================================ ========= ========= ======
operation                        time_sec  memory_mb counts
================================ ========= ========= ======
total compute_gmfs_and_curves    0.483     0.980     9     
total compute_ruptures           0.304     0.973     8     
managing sources                 0.160     0.0       1     
split/filter heavy sources       0.154     0.0       2     
building hazard curves           0.101     0.0       9     
reading composite source model   0.030     0.0       1     
filtering ruptures               0.016     0.0       9     
saving gmfs                      0.015     0.0       9     
saving ruptures                  0.011     0.0       8     
filtering composite source model 0.009     0.0       1     
aggregating hcurves              0.006     0.0       9     
reading exposure                 0.004     0.0       1     
store source_info                5.932E-04 0.0       1     
reading site collection          7.153E-06 0.0       1     
================================ ========= ========= ======