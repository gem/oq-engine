event based risk
================

Datastore /home/michele/ssd/calc_10534.hdf5 last updated Tue Apr 19 05:57:18 2016 on gem-tstation

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
oqlite_version               '0.13.0-git7c9cf8e'
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
event_based_risk_max_received_per_task 114444        
event_based_risk_num_tasks             7             
event_based_risk_sent.assetcol         30919         
event_based_risk_sent.monitor          18431         
event_based_risk_sent.riskinputs       32009         
event_based_risk_sent.riskmodel        75236         
event_based_risk_sent.rlzs_assoc       50540         
event_based_risk_tot_received          562931        
hostname                               'gem-tstation'
riskinputs.correl_model                810           
riskinputs.eids                        279           
riskinputs.eps                         4159          
riskinputs.gsims                       1496          
riskinputs.imt_taxonomies              1332          
riskinputs.imts                        432           
riskinputs.ses_ruptures                19308         
riskinputs.sitecol                     9135          
riskinputs.total                       36024         
riskinputs.trt_id                      45            
riskinputs.trunc_level                 108           
riskinputs.weight                      45            
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
0            1         SimpleFaultSource    482    15        0.002       0.047      0.260    
2            1         SimpleFaultSource    482    15        0.002       0.046      0.219    
1            2         SimpleFaultSource    4.000  1         0.002       0.0        0.010    
3            2         CharacteristicFaultS 1.000  1         0.001       0.0        0.004    
============ ========= ==================== ====== ========= =========== ========== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total event_based_risk         1.166     0.906     7     
computing individual risk      1.032     0.0       9     
total compute_ruptures         0.506     0.012     30    
compute poes                   0.171     0.0       18    
managing sources               0.170     0.0       1     
saving event loss tables       0.163     0.0       7     
total compute_gmfs_and_curves  0.156     0.723     7     
aggregate losses               0.156     0.0       99    
make contexts                  0.106     0.0       18    
getting hazard                 0.101     0.0       9     
splitting sources              0.094     0.0       2     
bulding hazard curves          0.037     0.0       7     
reading composite source model 0.026     0.0       1     
filtering ruptures             0.022     0.0       9     
compute and save statistics    0.016     0.0       1     
combine and save curves_by_rlz 0.014     0.0       1     
saving gmfs                    0.009     0.0       7     
aggregating hcurves            0.009     0.0       14    
filtering sources              0.007     0.0       4     
save curves_by_trt_gsim        0.007     0.0       1     
reading exposure               0.007     0.0       1     
store source_info              0.006     0.0       1     
saving ruptures                0.005     0.0       1     
aggregate curves               0.004     0.0       44    
reading site collection        8.106E-06 0.0       1     
============================== ========= ========= ======