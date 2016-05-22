classical risk
==============

gem-tstation:/home/michele/ssd/calc_16339.hdf5 updated Wed May 18 18:18:22 2016

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
oqlite_version               '0.13.0-git034c0a0'
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
====== ===================================== =========== ======================= =================
trt_id gsims                                 distances   siteparams              ruptparams       
====== ===================================== =========== ======================= =================
0      BooreAtkinson2008() ChiouYoungs2008() rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
1      AkkarBommer2010() ChiouYoungs2008()   rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
2      BooreAtkinson2008() ChiouYoungs2008() rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
3      AkkarBommer2010() ChiouYoungs2008()   rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
====== ===================================== =========== ======================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=8, rlzs=8)
  0,BooreAtkinson2008(): ['<0,b1,b11_b21,w=0.1125>', '<1,b1,b11_b22,w=0.075>']
  0,ChiouYoungs2008(): ['<2,b1,b12_b21,w=0.0375>', '<3,b1,b12_b22,w=0.025>']
  1,AkkarBommer2010(): ['<0,b1,b11_b21,w=0.1125>', '<2,b1,b12_b21,w=0.0375>']
  1,ChiouYoungs2008(): ['<1,b1,b11_b22,w=0.075>', '<3,b1,b12_b22,w=0.025>']
  2,BooreAtkinson2008(): ['<4,b2,b11_b21,w=0.3375>', '<5,b2,b11_b22,w=0.225>']
  2,ChiouYoungs2008(): ['<6,b2,b12_b21,w=0.1125>', '<7,b2,b12_b22,w=0.075>']
  3,AkkarBommer2010(): ['<4,b2,b11_b21,w=0.3375>', '<6,b2,b12_b21,w=0.1125>']
  3,ChiouYoungs2008(): ['<5,b2,b11_b22,w=0.225>', '<7,b2,b12_b22,w=0.075>']>

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

======== ===== ====== === === ========= ==========
taxonomy mean  stddev min max num_sites num_assets
tax1     1.000 0.0    1   1   4         4         
tax2     1.000 0.0    1   1   2         2         
tax3     1.000 NaN    1   1   1         1         
*ALL*    1.000 0.0    1   1   7         7         
======== ===== ====== === === ========= ==========

Slowest sources
---------------
============ ========= ========================= ====== ========= =========== ========== =========
trt_model_id source_id source_class              weight split_num filter_time split_time calc_time
============ ========= ========================= ====== ========= =========== ========== =========
0            1         SimpleFaultSource         482    15        0.002       0.030      2.527    
2            1         SimpleFaultSource         482    15        0.001       0.029      2.072    
3            2         CharacteristicFaultSource 1.000  1         0.001       0.0        0.030    
1            2         SimpleFaultSource         4.000  1         0.001       0.0        0.025    
============ ========= ========================= ====== ========= =========== ========== =========

Computation times by source typology
------------------------------------
========================= =========== ========== ========= ======
source_class              filter_time split_time calc_time counts
========================= =========== ========== ========= ======
CharacteristicFaultSource 0.001       0.0        0.030     1     
SimpleFaultSource         0.005       0.059      4.624     3     
========================= =========== ========== ========= ======

Information about the tasks
---------------------------
======================== ===== ====== ===== ===== =========
measurement              mean  stddev min   max   num_tasks
classical_risk.time_sec  0.075 0.060  0.016 0.155 8        
classical_risk.memory_mb 0.141 0.061  0.0   0.191 8        
classical.time_sec       0.170 0.064  0.030 0.263 28       
classical.memory_mb      0.479 0.766  0.0   1.863 28       
classical.time_sec       0.170 0.064  0.030 0.263 28       
classical.memory_mb      0.479 0.766  0.0   1.863 28       
======================== ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total classical                4.748     1.863     28    
making contexts                2.913     0.0       969   
computing poes                 1.516     0.0       1,938 
total classical_risk           0.601     0.191     8     
computing riskmodel            0.590     0.0       11    
managing sources               0.121     0.0       1     
splitting sources              0.059     0.0       2     
save curves_by_rlz             0.034     0.0       1     
store source_info              0.021     0.0       1     
compute and save statistics    0.021     0.0       1     
save curves_by_trt_gsim        0.020     0.0       1     
reading composite source model 0.017     0.0       1     
building hazard                0.007     0.0       8     
filtering sources              0.006     0.0       4     
reading exposure               0.006     0.0       1     
aggregate curves               0.003     0.0       28    
building riskinputs            0.001     0.0       1     
combine curves_by_rlz          0.001     0.0       1     
reading site collection        7.153E-06 0.0       1     
============================== ========= ========= ======