event based risk
================

Datastore /home/michele/ssd/calc_11421.hdf5 last updated Wed Apr 20 09:37:27 2016 on gem-tstation

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
oqlite_version               '0.13.0-git361357f'
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
event_based_risk_max_received_per_task 114486        
event_based_risk_num_tasks             7             
event_based_risk_sent.assetcol         30919         
event_based_risk_sent.monitor          18725         
event_based_risk_sent.riskinputs       32009         
event_based_risk_sent.riskmodel        75236         
event_based_risk_sent.rlzs_assoc       50589         
event_based_risk_tot_received          563225        
hostname                               'gem-tstation'
require_epsilons                       True          
====================================== ==============

Maximum memory allocated for the GMFs
-------------------------------------
The largest GMF block is for collection #1 of type 'Stable Shallow Crust',
contains 4 IMT(s), 7 site(s), 2 realization(s), and has a size of 896 B / num_tasks

Estimated data transfer for the avglosses
-----------------------------------------
7 asset(s) x 6 realization(s) x 5 loss type(s) x 2 losses x 8 bytes x 40 tasks = 131.25 KB

Exposure model
--------------
=========== =
#assets     7
#taxonomies 3
=========== =

======== =======
Taxonomy #Assets
======== =======
tax1     4      
tax2     2      
tax3     1      
======== =======

Slowest sources
---------------
============ ========= ==================== ====== ========= =========== ========== =========
trt_model_id source_id source_class         weight split_num filter_time split_time calc_time
============ ========= ==================== ====== ========= =========== ========== =========
0            1         SimpleFaultSource    482    15        0.002       0.041      0.282    
2            1         SimpleFaultSource    482    15        0.001       0.039      0.269    
1            2         SimpleFaultSource    4.000  1         0.002       0.0        0.020    
3            2         CharacteristicFaultS 1.000  1         0.001       0.0        0.004    
============ ========= ==================== ====== ========= =========== ========== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total event_based_risk         1.106     0.871     7     
computing individual risk      0.968     0.0       9     
total compute_ruptures         0.587     0.008     30    
saving event loss tables       0.166     0.0       7     
compute poes                   0.161     0.0       18    
aggregate losses               0.154     0.0       99    
managing sources               0.149     0.0       1     
total compute_gmfs_and_curves  0.126     0.844     7     
getting hazard                 0.106     0.0       9     
make contexts                  0.102     0.0       18    
splitting sources              0.079     0.0       2     
bulding hazard curves          0.028     0.0       7     
filtering ruptures             0.026     0.0       9     
reading composite source model 0.021     0.0       1     
compute and save statistics    0.014     0.0       1     
combine and save curves_by_rlz 0.012     0.0       1     
saving gmfs                    0.009     0.0       7     
aggregating hcurves            0.009     0.0       14    
filtering sources              0.006     0.0       4     
save curves_by_trt_gsim        0.006     0.0       1     
store source_info              0.006     0.0       1     
reading exposure               0.005     0.0       1     
saving ruptures                0.005     0.0       1     
aggregate curves               0.004     0.0       44    
reading site collection        7.153E-06 0.0       1     
============================== ========= ========= ======