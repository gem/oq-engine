event based risk
================

============== ===================
checksum32     3,029,642,047      
date           2018-05-15T04:12:57
engine_version 3.1.0-git0acbc11   
============== ===================

num_sites = 7, num_levels = 46

Parameters
----------
=============================== ==================
calculation_mode                'event_based_risk'
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              1.0               
ses_per_logic_tree_path         10                
truncation_level                3.0               
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                0.1               
area_source_discretization      10.0              
ground_motion_correlation_model 'JB2009'          
minimum_intensity               {}                
random_seed                     24                
master_seed                     0                 
ses_seed                        42                
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
source                              `6.05.xml <6.05.xml>`_                                                          
source                              `source_model_1.xml <source_model_1.xml>`_                                      
source                              `source_model_2.xml <source_model_2.xml>`_                                      
source_model_logic_tree             `source_model_logic_tree.xml <source_model_logic_tree.xml>`_                    
structural_vulnerability            `structural_vulnerability_model.xml <structural_vulnerability_model.xml>`_      
=================================== ================================================================================

Composite source model
----------------------
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
b1        0.25000 complex(2,2,1)  4/4             
b2        0.25000 complex(2,2,1)  4/4             
b3        0.50000 complex(2,2,1)  1/1             
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ===================================== =========== ======================= =================
grp_id gsims                                 distances   siteparams              ruptparams       
====== ===================================== =========== ======================= =================
0      BooreAtkinson2008() ChiouYoungs2008() rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
1      AkkarBommer2010() ChiouYoungs2008()   rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
2      BooreAtkinson2008() ChiouYoungs2008() rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
3      AkkarBommer2010() ChiouYoungs2008()   rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
4      MontalvaEtAl2016SSlab()               rhypo rjb   backarc vs30            hypo_depth mag   
====== ===================================== =========== ======================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=9, rlzs=9)
  0,BooreAtkinson2008(): [0 1]
  0,ChiouYoungs2008(): [2 3]
  1,AkkarBommer2010(): [0 2]
  1,ChiouYoungs2008(): [1 3]
  2,BooreAtkinson2008(): [4 5]
  2,ChiouYoungs2008(): [6 7]
  3,AkkarBommer2010(): [4 6]
  3,ChiouYoungs2008(): [5 7]
  4,MontalvaEtAl2016SSlab(): [8]>

Number of ruptures per tectonic region type
-------------------------------------------
================== ====== ==================== ============ ============
source_model       grp_id trt                  eff_ruptures tot_ruptures
================== ====== ==================== ============ ============
source_model_1.xml 0      Active Shallow Crust 482          482         
source_model_1.xml 1      Stable Shallow Crust 4            4           
source_model_2.xml 2      Active Shallow Crust 482          482         
source_model_2.xml 3      Stable Shallow Crust 1            1           
6.05.xml           4      Deep Seismicity      2            2           
================== ====== ==================== ============ ============

============= ===
#TRT models   5  
#eff_ruptures 971
#tot_ruptures 971
#tot_weight   971
============= ===

Estimated data transfer for the avglosses
-----------------------------------------
7 asset(s) x 9 realization(s) x 5 loss type(s) x 2 losses x 8 bytes x 60 tasks = 295.31 KB

Exposure model
--------------
=============== ========
#assets         7       
#taxonomies     3       
deductibile     absolute
insurance_limit absolute
=============== ========

======== ======= ====== === === ========= ==========
taxonomy mean    stddev min max num_sites num_assets
tax1     1.00000 0.0    1   1   4         4         
tax2     1.00000 0.0    1   1   2         2         
tax3     1.00000 NaN    1   1   1         1         
*ALL*    1.00000 0.0    1   1   7         7         
======== ======= ====== === === ========= ==========

Slowest sources
---------------
========= ========================== ============ ========= ========== ========= ========= ======
source_id source_class               num_ruptures calc_time split_time num_sites num_split events
========= ========================== ============ ========= ========== ========= ========= ======
1         SimpleFaultSource          2            0.50110   0.0        210       30        1     
2         CharacteristicFaultSource  1            0.01897   0.0        14        2         9     
buc06pt05 NonParametricSeismicSource 1            0.00355   0.0        14        2         2     
========= ========================== ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
========================== ========= ======
source_class               calc_time counts
========================== ========= ======
CharacteristicFaultSource  0.01897   1     
NonParametricSeismicSource 0.00355   1     
SimpleFaultSource          0.50110   1     
========================== ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =========
operation-duration mean    stddev  min     max     num_tasks
prefilter          0.00616 0.00299 0.00182 0.01126 34       
compute_ruptures   0.04040 0.02050 0.00217 0.06691 15       
================== ======= ======= ======= ======= =========

Informational data
------------------
================ ================================================================================= ========
task             sent                                                                              received
prefilter        srcs=53.47 KB monitor=10.72 KB srcfilter=7.6 KB                                   55.63 KB
compute_ruptures sources=35.58 KB param=16.64 KB src_filter=15.29 KB monitor=4.83 KB gsims=3.13 KB 16.25 KB
================ ================================================================================= ========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total compute_ruptures         0.60597   2.61719   15    
managing sources               0.24545   0.0       1     
total prefilter                0.20931   4.63281   34    
reading composite source model 0.02199   0.0       1     
making contexts                0.01881   0.0       6     
saving ruptures                0.00862   0.0       15    
store source_info              0.00598   0.0       1     
reading site collection        0.00513   0.0       1     
unpickling prefilter           0.00370   0.0       34    
reading exposure               0.00177   0.0       1     
setting event years            0.00177   0.0       1     
unpickling compute_ruptures    0.00104   0.0       15    
splitting sources              7.994E-04 0.0       1     
============================== ========= ========= ======