event based risk
================

============== ===================
checksum32     571,516,522        
date           2018-09-05T10:04:23
engine_version 3.2.0-gitb4ef3a4b6c
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
source                              `6.05.hdf5 <6.05.hdf5>`_                                                        
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
4      MontalvaEtAl2016SSlab()               rhypo rrup  backarc vs30            hypo_depth mag   
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
6.05.hdf5          4      Deep Seismicity      2            2           
================== ====== ==================== ============ ============

============= ===
#TRT models   5  
#eff_ruptures 971
#tot_ruptures 971
#tot_weight   0  
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
1         SimpleFaultSource          482          0.49136   4.039E-04  7.00000   30        1     
2         CharacteristicFaultSource  1            0.01853   1.454E-05  7.00000   2         9     
buc06pt05 NonParametricSeismicSource 2            0.00163   3.529E-05  7.00000   2         1     
========= ========================== ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
========================== ========= ======
source_class               calc_time counts
========================== ========= ======
CharacteristicFaultSource  0.01853   1     
NonParametricSeismicSource 0.00163   1     
SimpleFaultSource          0.49136   1     
========================== ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
==================== ======= ======= ======= ======= =========
operation-duration   mean    stddev  min     max     num_tasks
pickle_source_models 0.01648 0.00507 0.01264 0.02222 3        
preprocess           0.03040 0.01376 0.00456 0.05587 31       
compute_gmfs         0.03609 0.01965 0.02051 0.05816 3        
==================== ======= ======= ======= ======= =========

Data transfer
-------------
==================== ================================================================================================= ========
task                 sent                                                                                              received
pickle_source_models monitor=1.01 KB converter=867 B fnames=576 B                                                      495 B   
preprocess           srcs=51.23 KB param=19.28 KB monitor=10.81 KB srcfilter=7.66 KB                                   64.89 KB
compute_gmfs         param=17.09 KB sources_or_ruptures=13.62 KB rlzs_by_gsim=1.12 KB monitor=1.01 KB src_filter=660 B 57.45 KB
==================== ================================================================================================= ========

Slowest operations
------------------
========================== ======== ========= ======
operation                  time_sec memory_mb counts
========================== ======== ========= ======
total preprocess           0.94243  9.18750   31    
total compute_gmfs         0.10827  1.16797   3     
building hazard            0.07512  1.16016   3     
total pickle_source_models 0.04945  6.08203   3     
building hazard curves     0.01827  0.0       63    
making contexts            0.01682  0.0       6     
saving ruptures            0.01098  0.0       3     
building ruptures          0.00852  0.0       3     
saving gmfs                0.00678  0.0       3     
store source_info          0.00627  0.0       1     
managing sources           0.00474  0.0       1     
saving gmf_data/indices    0.00392  0.0       1     
aggregating hcurves        0.00343  0.0       3     
GmfGetter.init             0.00277  0.06250   3     
splitting sources          0.00172  0.0       1     
setting event years        0.00149  0.0       1     
reading exposure           0.00132  0.0       1     
========================== ======== ========= ======