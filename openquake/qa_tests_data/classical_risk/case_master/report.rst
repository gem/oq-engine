classical risk
==============

gem-tstation:/home/michele/ssd/calc_955.hdf5 updated Thu Apr 28 15:38:28 2016

num_sites = 7, sitecol = 1015 B

Parameters
----------
============================ ===================
calculation_mode             'classical_risk'   
number_of_logic_tree_samples 0                  
maximum_distance             {'default': 200.0} 
investigation_time           50.0               
ses_per_logic_tree_path      1                  
truncation_level             3.0                
rupture_mesh_spacing         2.0                
complex_fault_mesh_spacing   2.0                
width_of_mfd_bin             0.1                
area_source_discretization   10.0               
random_seed                  24                 
master_seed                  0                  
avg_losses                   False              
sites_per_tile               1000               
oqlite_version               '0.13.0-git93d6f64'
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
b2        0.750  `source_model_2.xml <source_model_2.xml>`_ complex(2,2)    4/4             
========= ====== ========================================== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================================= =========== ======================= =================
trt_id gsims                             distances   siteparams              ruptparams       
====== ================================= =========== ======================= =================
0      BooreAtkinson2008 ChiouYoungs2008 rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
1      AkkarBommer2010 ChiouYoungs2008   rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
2      BooreAtkinson2008 ChiouYoungs2008 rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
3      AkkarBommer2010 ChiouYoungs2008   rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
====== ================================= =========== ======================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=8, rlzs=8)
  0,BooreAtkinson2008: ['<0,b1,b11_b21,w=0.1125>', '<1,b1,b11_b22,w=0.075>']
  0,ChiouYoungs2008: ['<2,b1,b12_b21,w=0.0375>', '<3,b1,b12_b22,w=0.025>']
  1,AkkarBommer2010: ['<0,b1,b11_b21,w=0.1125>', '<2,b1,b12_b21,w=0.0375>']
  1,ChiouYoungs2008: ['<1,b1,b11_b22,w=0.075>', '<3,b1,b12_b22,w=0.025>']
  2,BooreAtkinson2008: ['<4,b2,b11_b21,w=0.3375>', '<5,b2,b11_b22,w=0.225>']
  2,ChiouYoungs2008: ['<6,b2,b12_b21,w=0.1125>', '<7,b2,b12_b22,w=0.075>']
  3,AkkarBommer2010: ['<4,b2,b11_b21,w=0.3375>', '<6,b2,b12_b21,w=0.1125>']
  3,ChiouYoungs2008: ['<5,b2,b11_b22,w=0.225>', '<7,b2,b12_b22,w=0.075>']>

Number of ruptures per tectonic region type
-------------------------------------------
================== ====== ==================== =========== ============ ======
source_model       trt_id trt                  num_sources eff_ruptures weight
================== ====== ==================== =========== ============ ======
source_model_1.xml 0      Active Shallow Crust 1           482          482   
source_model_1.xml 1      Stable Shallow Crust 1           4            4.000 
source_model_2.xml 2      Active Shallow Crust 1           482          482   
source_model_2.xml 3      Stable Shallow Crust 1           1            1.000 
================== ====== ==================== =========== ============ ======

=============== ===
#TRT models     4  
#sources        4  
#eff_ruptures   969
filtered_weight 969
=============== ===

Informational data
------------------
================ ==============
hostname         'gem-tstation'
require_epsilons True          
================ ==============

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
0            1         SimpleFaultSource    482    15        0.016       0.111      9.583    
2            1         SimpleFaultSource    482    15        0.003       0.082      9.319    
3            2         CharacteristicFaultS 1.000  1         0.002       0.0        0.064    
1            2         SimpleFaultSource    4.000  1         0.003       0.0        0.049    
============ ========= ==================== ====== ========= =========== ========== =========

Information about the tasks
---------------------------
======================== ===== ===== ===== ======
measurement              min   max   mean  stddev
classical_risk.time_sec  0.033 0.275 0.160 0.086 
classical_risk.memory_mb 0.008 0.297 0.123 0.103 
classical.time_sec       0.054 1.115 0.639 0.279 
classical.memory_mb      0.0   3.734 1.212 1.149 
classical.time_sec       0.054 1.115 0.639 0.279 
classical.memory_mb      0.0   3.734 1.212 1.149 
======================== ===== ===== ===== ======

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total classical                19        3.734     30    
making contexts                11        0.0       969   
computing poes                 6.473     0.0       1,938 
total classical_risk           1.761     0.297     11    
computing risk                 1.752     0.0       11    
managing sources               0.369     0.0       1     
splitting sources              0.192     0.0       2     
save curves_by_rlz             0.069     0.0       1     
compute and save statistics    0.044     0.0       1     
reading composite source model 0.044     0.0       1     
store source_info              0.040     0.0       1     
reading exposure               0.026     0.0       1     
save curves_by_trt_gsim        0.026     0.0       1     
filtering sources              0.024     0.0       4     
aggregate curves               0.006     0.0       30    
building hazard                0.005     0.0       11    
building riskinputs            0.003     0.0       1     
combine curves_by_rlz          0.002     0.0       1     
reading site collection        1.097E-05 0.0       1     
============================== ========= ========= ======