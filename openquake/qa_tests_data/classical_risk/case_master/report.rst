classical risk
==============

num_sites = 7, sitecol = 960 B

Parameters
----------
============================ ==============
calculation_mode             classical_risk
number_of_logic_tree_samples 0             
maximum_distance             200           
investigation_time           50            
ses_per_logic_tree_path      1             
truncation_level             3.000         
rupture_mesh_spacing         2.000         
complex_fault_mesh_spacing   2.000         
width_of_mfd_bin             0.100         
area_source_discretization   10            
random_seed                  24            
master_seed                  0             
concurrent_tasks             16            
avg_losses                   False         
sites_per_tile               1000          
============================ ==============

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

Expected data transfer for the sources
--------------------------------------
=========================== =========
Number of tasks to generate 22       
Sent data                   287.07 KB
Total received data         188.9 KB 
Maximum received per task   8.61 KB  
=========================== =========

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
2            1         SimpleFaultSource    482    15        0.002       0.058      6.148    
0            1         SimpleFaultSource    482    15        0.004       0.070      5.743    
1            2         SimpleFaultSource    4.000  1         0.002       0.0        0.029    
3            2         CharacteristicFaultS 1.000  1         0.002       0.0        0.026    
============ ========= ==================== ====== ========= =========== ========== =========