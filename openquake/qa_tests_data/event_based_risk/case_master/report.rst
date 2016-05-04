event based risk
================

gem-tstation:/home/michele/ssd/calc_12616.hdf5 updated Wed May  4 04:54:29 2016

num_sites = 7, sitecol = 1015 B

Parameters
----------
============================ ===================
calculation_mode             'event_based_risk' 
number_of_logic_tree_samples 0                  
maximum_distance             {'default': 200.0} 
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
oqlite_version               '0.13.0-git02c4b55'
============================ ===================

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
source_model_logic_tree             `source_model_logic_tree.xml <source_model_logic_tree.xml>`_                    
structural_vulnerability            `structural_vulnerability_model.xml <structural_vulnerability_model.xml>`_      
=================================== ================================================================================

Composite source model
----------------------
========= ====== ========================================== =============== ================
smlt_path weight source_model_file                          gsim_logic_tree num_realizations
========= ====== ========================================== =============== ================
b1        0.250  `source_model_1.xml <source_model_1.xml>`_ complex(2,2)    4/4             
b2        0.750  `source_model_2.xml <source_model_2.xml>`_ simple(2,0)     2/2             
========= ====== ========================================== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================================= =========== ======================= =================
trt_id gsims                             distances   siteparams              ruptparams       
====== ================================= =========== ======================= =================
0      BooreAtkinson2008 ChiouYoungs2008 rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
1      AkkarBommer2010 ChiouYoungs2008   rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
2      BooreAtkinson2008 ChiouYoungs2008 rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
====== ================================= =========== ======================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=6, rlzs=6)
  0,BooreAtkinson2008: ['<0,b1,b11_b21,w=0.1125>', '<1,b1,b11_b22,w=0.075>']
  0,ChiouYoungs2008: ['<2,b1,b12_b21,w=0.0375>', '<3,b1,b12_b22,w=0.025>']
  1,AkkarBommer2010: ['<0,b1,b11_b21,w=0.1125>', '<2,b1,b12_b21,w=0.0375>']
  1,ChiouYoungs2008: ['<1,b1,b11_b22,w=0.075>', '<3,b1,b12_b22,w=0.025>']
  2,BooreAtkinson2008: ['<4,b2,b11_@,w=0.5625>']
  2,ChiouYoungs2008: ['<5,b2,b12_@,w=0.1875>']>

Number of ruptures per tectonic region type
-------------------------------------------
================== ====== ==================== =========== ============ ======
source_model       trt_id trt                  num_sources eff_ruptures weight
================== ====== ==================== =========== ============ ======
source_model_1.xml 0      Active Shallow Crust 1           1            482   
source_model_1.xml 1      Stable Shallow Crust 1           4            4.000 
source_model_2.xml 2      Active Shallow Crust 1           4            482   
================== ====== ==================== =========== ============ ======

=============== ===
#TRT models     3  
#sources        3  
#eff_ruptures   9  
filtered_weight 968
=============== ===

Informational data
------------------
====================================== ==============
event_based_risk_max_received_per_task 101500        
event_based_risk_num_tasks             6             
event_based_risk_sent.assetcol         26502         
event_based_risk_sent.monitor          16260         
event_based_risk_sent.riskinput        28221         
event_based_risk_sent.riskmodel        56424         
event_based_risk_sent.rlzs_assoc       41574         
event_based_risk_tot_received          456308        
hostname                               'gem-tstation'
require_epsilons                       True          
====================================== ==============

Specific information for event based
------------------------------------
======================== ===
Total number of ruptures 9  
Total number of events   106
Rupture multiplicity     11 
======================== ===

Maximum memory allocated for the GMFs
-------------------------------------
The largest GMF block is for trt_model_id=1, contains 4 IMT(s), 4 realization(s)
and has a size of 44.19 KB / num_tasks

Estimated data transfer for the avglosses
-----------------------------------------
7 asset(s) x 6 realization(s) x 5 loss type(s) x 2 losses x 8 bytes x 40 tasks = 131.25 KB

Exposure model
--------------
=========== =
#assets     7
#taxonomies 3
=========== =

======== ===== ====== === === ========= ==========
taxonomy mean  stddev min max num_sites num_assets
tax1     1.000 0.0    1   1   4         4         
tax2     1.000 0.0    1   1   2         2         
tax3     1.000 NaN    1   1   1         1         
*ALL*    1.000 0.0    1   1   7         7         
======== ===== ====== === === ========= ==========

Slowest sources
---------------
============ ========= ==================== ====== ========= =========== ========== =========
trt_model_id source_id source_class         weight split_num filter_time split_time calc_time
============ ========= ==================== ====== ========= =========== ========== =========
0            1         SimpleFaultSource    482    15        0.002       0.041      0.326    
2            1         SimpleFaultSource    482    15        0.001       0.037      0.277    
1            2         SimpleFaultSource    4.000  1         0.001       0.0        0.026    
3            2         CharacteristicFaultS 1.000  1         0.001       0.0        0.006    
============ ========= ==================== ====== ========= =========== ========== =========

Information about the tasks
---------------------------
================================= ========= ====== ===== ===== =========
measurement                       mean      stddev min   max   num_tasks
compute_ruptures.time_sec         0.022     0.010  0.006 0.050 30       
compute_ruptures.memory_mb        6.510E-04 0.002  0.0   0.008 30       
compute_gmfs_and_curves.time_sec  0.042     0.008  0.031 0.056 6        
compute_gmfs_and_curves.memory_mb 0.0       0.0    0.0   0.0   6        
event_based_risk.time_sec         0.205     0.071  0.123 0.293 6        
event_based_risk.memory_mb        0.024     0.027  0.0   0.055 6        
================================= ========= ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total event_based_risk         1.227     0.055     6     
computing riskmodel            0.973     0.0       66    
total compute_ruptures         0.649     0.008     30    
aggregate losses               0.588     0.0       66    
compute poes                   0.330     0.0       18    
total compute_gmfs_and_curves  0.253     0.0       6     
building hazard                0.203     0.0       6     
saving event loss tables       0.188     0.0       6     
managing sources               0.150     0.0       1     
splitting sources              0.078     0.0       2     
make contexts                  0.076     0.0       18    
bulding hazard curves          0.043     0.0       6     
reading composite source model 0.021     0.0       1     
filtering ruptures             0.021     0.0       9     
compute and save statistics    0.020     0.0       1     
aggregating hcurves            0.018     0.0       22    
save curves_by_rlz             0.017     0.0       1     
saving gmfs                    0.012     0.0       22    
saving ruptures                0.008     0.0       1     
store source_info              0.007     0.0       1     
filtering sources              0.006     0.0       4     
aggregate curves               0.006     0.0       52    
reading exposure               0.005     0.0       1     
reading site collection        5.960E-06 0.0       1     
============================== ========= ========= ======