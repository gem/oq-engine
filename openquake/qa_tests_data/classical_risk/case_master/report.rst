classical risk
==============

============================================ ========================
gem-tstation:/mnt/ssd/oqdata/calc_85507.hdf5 Tue Feb 14 15:36:34 2017
engine_version                               2.3.0-git1f56df2        
hazardlib_version                            0.23.0-git6937706       
============================================ ========================

num_sites = 7, sitecol = 1.11 KB

Parameters
----------
=============================== ==================
calculation_mode                'classical_risk'  
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              50.0              
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                0.1               
area_source_discretization      10.0              
ground_motion_correlation_model None              
random_seed                     24                
master_seed                     0                 
avg_losses                      False             
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
b1        0.250  `source_model_1.xml <source_model_1.xml>`_ complex(2,2)    4/4             
b2        0.750  `source_model_2.xml <source_model_2.xml>`_ complex(2,2)    4/4             
========= ====== ========================================== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ===================================== =========== ======================= =================
grp_id gsims                                 distances   siteparams              ruptparams       
====== ===================================== =========== ======================= =================
0      BooreAtkinson2008() ChiouYoungs2008() rrup rjb rx vs30 z1pt0 vs30measured mag dip rake ztor
1      AkkarBommer2010() ChiouYoungs2008()   rrup rjb rx vs30 z1pt0 vs30measured mag dip rake ztor
2      BooreAtkinson2008() ChiouYoungs2008() rrup rjb rx vs30 z1pt0 vs30measured mag dip rake ztor
3      AkkarBommer2010() ChiouYoungs2008()   rrup rjb rx vs30 z1pt0 vs30measured mag dip rake ztor
====== ===================================== =========== ======================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=8, rlzs=8)
  0,BooreAtkinson2008(): ['<0,b1~b11_b21,w=0.1125>', '<1,b1~b11_b22,w=0.075>']
  0,ChiouYoungs2008(): ['<2,b1~b12_b21,w=0.0375>', '<3,b1~b12_b22,w=0.025>']
  1,AkkarBommer2010(): ['<0,b1~b11_b21,w=0.1125>', '<2,b1~b12_b21,w=0.0375>']
  1,ChiouYoungs2008(): ['<1,b1~b11_b22,w=0.075>', '<3,b1~b12_b22,w=0.025>']
  2,BooreAtkinson2008(): ['<4,b2~b11_b21,w=0.3375>', '<5,b2~b11_b22,w=0.22499999999999998>']
  2,ChiouYoungs2008(): ['<6,b2~b12_b21,w=0.11249999999999999>', '<7,b2~b12_b22,w=0.07500000000000001>']
  3,AkkarBommer2010(): ['<4,b2~b11_b21,w=0.3375>', '<6,b2~b12_b21,w=0.11249999999999999>']
  3,ChiouYoungs2008(): ['<5,b2~b11_b22,w=0.22499999999999998>', '<7,b2~b12_b22,w=0.07500000000000001>']>

Number of ruptures per tectonic region type
-------------------------------------------
================== ====== ==================== =========== ============ ============
source_model       grp_id trt                  num_sources eff_ruptures tot_ruptures
================== ====== ==================== =========== ============ ============
source_model_1.xml 0      Active Shallow Crust 1           482          482         
source_model_1.xml 1      Stable Shallow Crust 1           4            4           
source_model_2.xml 2      Active Shallow Crust 1           482          482         
source_model_2.xml 3      Stable Shallow Crust 1           1            1           
================== ====== ==================== =========== ============ ============

============= ===
#TRT models   4  
#sources      4  
#eff_ruptures 969
#tot_ruptures 969
#tot_weight   969
============= ===

Informational data
------------------
=========================================== ============
count_eff_ruptures_max_received_per_task    1,747       
count_eff_ruptures_num_tasks                8           
count_eff_ruptures_sent.gsims               1,424       
count_eff_ruptures_sent.monitor             12,176      
count_eff_ruptures_sent.sources             22,487      
count_eff_ruptures_sent.srcfilter           7,024       
count_eff_ruptures_tot_received             13,976      
hazard.input_weight                         969         
hazard.n_imts                               4           
hazard.n_levels                             40          
hazard.n_realizations                       8           
hazard.n_sites                              7           
hazard.n_sources                            4           
hazard.output_weight                        2,240       
hostname                                    gem-tstation
require_epsilons                            1           
=========================================== ============

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
3      2         CharacteristicFaultSource 1            0.0       7         0        
0      1         SimpleFaultSource         482          0.0       7         0        
2      1         SimpleFaultSource         482          0.0       7         0        
1      2         SimpleFaultSource         4            0.0       7         0        
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
count_eff_ruptures 0.283 0.171  0.019 0.454 8        
================== ===== ====== ===== ===== =========

Slowest operations
------------------
================================ ========= ========= ======
operation                        time_sec  memory_mb counts
================================ ========= ========= ======
total count_eff_ruptures         2.263     3.969     8     
managing sources                 0.137     0.0       1     
reading composite source model   0.033     0.0       1     
filtering composite source model 0.010     0.0       1     
reading exposure                 0.006     0.0       1     
store source_info                9.756E-04 0.0       1     
aggregate curves                 1.588E-04 0.0       8     
saving probability maps          4.315E-05 0.0       1     
reading site collection          1.001E-05 0.0       1     
================================ ========= ========= ======