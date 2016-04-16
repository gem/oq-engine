Classical PSHA with non-trivial logic tree (1 source model + relative uncertainties on G-R b value and maximum magnitude and 2 GMPEs per tectonic region type)
==============================================================================================================================================================

num_sites = 1, sitecol = 739 B

Parameters
----------
============================ ===================
calculation_mode             'classical'        
number_of_logic_tree_samples 0                  
maximum_distance             {'default': 200.0} 
investigation_time           50.0               
ses_per_logic_tree_path      1                  
truncation_level             3.0                
rupture_mesh_spacing         2.0                
complex_fault_mesh_spacing   2.0                
width_of_mfd_bin             0.1                
area_source_discretization   5.0                
random_seed                  23                 
master_seed                  0                  
concurrent_tasks             40                 
sites_per_tile               1000               
oqlite_version               '0.13.0-gite77b1a1'
============================ ===================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
source                  `source_model.xml <source_model.xml>`_                      
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
=========== ====== ====================================== =============== ================
smlt_path   weight source_model_file                      gsim_logic_tree num_realizations
=========== ====== ====================================== =============== ================
b11_b21_b31 0.111  `source_model.xml <source_model.xml>`_ complex(2,2)    4/4             
b11_b21_b32 0.111  `source_model.xml <source_model.xml>`_ complex(2,2)    4/4             
b11_b21_b33 0.111  `source_model.xml <source_model.xml>`_ complex(2,2)    4/4             
b11_b22_b31 0.111  `source_model.xml <source_model.xml>`_ complex(2,2)    4/4             
b11_b22_b32 0.111  `source_model.xml <source_model.xml>`_ complex(2,2)    4/4             
b11_b22_b33 0.111  `source_model.xml <source_model.xml>`_ complex(2,2)    4/4             
b11_b23_b31 0.111  `source_model.xml <source_model.xml>`_ complex(2,2)    4/4             
b11_b23_b32 0.111  `source_model.xml <source_model.xml>`_ complex(2,2)    4/4             
b11_b23_b33 0.112  `source_model.xml <source_model.xml>`_ complex(2,2)    4/4             
=========== ====== ====================================== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================================= =========== ======================= =================
trt_id gsims                             distances   siteparams              ruptparams       
====== ================================= =========== ======================= =================
0      BooreAtkinson2008 ChiouYoungs2008 rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
1      Campbell2003 ToroEtAl2002         rjb rrup                            mag              
2      BooreAtkinson2008 ChiouYoungs2008 rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
3      Campbell2003 ToroEtAl2002         rjb rrup                            mag              
4      BooreAtkinson2008 ChiouYoungs2008 rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
5      Campbell2003 ToroEtAl2002         rjb rrup                            mag              
6      BooreAtkinson2008 ChiouYoungs2008 rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
7      Campbell2003 ToroEtAl2002         rjb rrup                            mag              
8      BooreAtkinson2008 ChiouYoungs2008 rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
9      Campbell2003 ToroEtAl2002         rjb rrup                            mag              
10     BooreAtkinson2008 ChiouYoungs2008 rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
11     Campbell2003 ToroEtAl2002         rjb rrup                            mag              
12     BooreAtkinson2008 ChiouYoungs2008 rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
13     Campbell2003 ToroEtAl2002         rjb rrup                            mag              
14     BooreAtkinson2008 ChiouYoungs2008 rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
15     Campbell2003 ToroEtAl2002         rjb rrup                            mag              
16     BooreAtkinson2008 ChiouYoungs2008 rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
17     Campbell2003 ToroEtAl2002         rjb rrup                            mag              
====== ================================= =========== ======================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=36, rlzs=36)
  0,BooreAtkinson2008: ['<0,b11_b21_b31,b11_b21,w=0.02772225>', '<1,b11_b21_b31,b11_b22,w=0.02772225>']
  0,ChiouYoungs2008: ['<2,b11_b21_b31,b12_b21,w=0.02772225>', '<3,b11_b21_b31,b12_b22,w=0.02772225>']
  1,Campbell2003: ['<1,b11_b21_b31,b11_b22,w=0.02772225>', '<3,b11_b21_b31,b12_b22,w=0.02772225>']
  1,ToroEtAl2002: ['<0,b11_b21_b31,b11_b21,w=0.02772225>', '<2,b11_b21_b31,b12_b21,w=0.02772225>']
  2,BooreAtkinson2008: ['<4,b11_b21_b32,b11_b21,w=0.02772225>', '<5,b11_b21_b32,b11_b22,w=0.02772225>']
  2,ChiouYoungs2008: ['<6,b11_b21_b32,b12_b21,w=0.02772225>', '<7,b11_b21_b32,b12_b22,w=0.02772225>']
  3,Campbell2003: ['<5,b11_b21_b32,b11_b22,w=0.02772225>', '<7,b11_b21_b32,b12_b22,w=0.02772225>']
  3,ToroEtAl2002: ['<4,b11_b21_b32,b11_b21,w=0.02772225>', '<6,b11_b21_b32,b12_b21,w=0.02772225>']
  4,BooreAtkinson2008: ['<8,b11_b21_b33,b11_b21,w=0.0278055>', '<9,b11_b21_b33,b11_b22,w=0.0278055>']
  4,ChiouYoungs2008: ['<10,b11_b21_b33,b12_b21,w=0.0278055>', '<11,b11_b21_b33,b12_b22,w=0.0278055>']
  5,Campbell2003: ['<9,b11_b21_b33,b11_b22,w=0.0278055>', '<11,b11_b21_b33,b12_b22,w=0.0278055>']
  5,ToroEtAl2002: ['<8,b11_b21_b33,b11_b21,w=0.0278055>', '<10,b11_b21_b33,b12_b21,w=0.0278055>']
  6,BooreAtkinson2008: ['<12,b11_b22_b31,b11_b21,w=0.02772225>', '<13,b11_b22_b31,b11_b22,w=0.02772225>']
  6,ChiouYoungs2008: ['<14,b11_b22_b31,b12_b21,w=0.02772225>', '<15,b11_b22_b31,b12_b22,w=0.02772225>']
  7,Campbell2003: ['<13,b11_b22_b31,b11_b22,w=0.02772225>', '<15,b11_b22_b31,b12_b22,w=0.02772225>']
  7,ToroEtAl2002: ['<12,b11_b22_b31,b11_b21,w=0.02772225>', '<14,b11_b22_b31,b12_b21,w=0.02772225>']
  8,BooreAtkinson2008: ['<16,b11_b22_b32,b11_b21,w=0.02772225>', '<17,b11_b22_b32,b11_b22,w=0.02772225>']
  8,ChiouYoungs2008: ['<18,b11_b22_b32,b12_b21,w=0.02772225>', '<19,b11_b22_b32,b12_b22,w=0.02772225>']
  9,Campbell2003: ['<17,b11_b22_b32,b11_b22,w=0.02772225>', '<19,b11_b22_b32,b12_b22,w=0.02772225>']
  9,ToroEtAl2002: ['<16,b11_b22_b32,b11_b21,w=0.02772225>', '<18,b11_b22_b32,b12_b21,w=0.02772225>']
  10,BooreAtkinson2008: ['<20,b11_b22_b33,b11_b21,w=0.0278055>', '<21,b11_b22_b33,b11_b22,w=0.0278055>']
  10,ChiouYoungs2008: ['<22,b11_b22_b33,b12_b21,w=0.0278055>', '<23,b11_b22_b33,b12_b22,w=0.0278055>']
  11,Campbell2003: ['<21,b11_b22_b33,b11_b22,w=0.0278055>', '<23,b11_b22_b33,b12_b22,w=0.0278055>']
  11,ToroEtAl2002: ['<20,b11_b22_b33,b11_b21,w=0.0278055>', '<22,b11_b22_b33,b12_b21,w=0.0278055>']
  12,BooreAtkinson2008: ['<24,b11_b23_b31,b11_b21,w=0.0278055>', '<25,b11_b23_b31,b11_b22,w=0.0278055>']
  12,ChiouYoungs2008: ['<26,b11_b23_b31,b12_b21,w=0.0278055>', '<27,b11_b23_b31,b12_b22,w=0.0278055>']
  13,Campbell2003: ['<25,b11_b23_b31,b11_b22,w=0.0278055>', '<27,b11_b23_b31,b12_b22,w=0.0278055>']
  13,ToroEtAl2002: ['<24,b11_b23_b31,b11_b21,w=0.0278055>', '<26,b11_b23_b31,b12_b21,w=0.0278055>']
  14,BooreAtkinson2008: ['<28,b11_b23_b32,b11_b21,w=0.0278055>', '<29,b11_b23_b32,b11_b22,w=0.0278055>']
  14,ChiouYoungs2008: ['<30,b11_b23_b32,b12_b21,w=0.0278055>', '<31,b11_b23_b32,b12_b22,w=0.0278055>']
  15,Campbell2003: ['<29,b11_b23_b32,b11_b22,w=0.0278055>', '<31,b11_b23_b32,b12_b22,w=0.0278055>']
  15,ToroEtAl2002: ['<28,b11_b23_b32,b11_b21,w=0.0278055>', '<30,b11_b23_b32,b12_b21,w=0.0278055>']
  16,BooreAtkinson2008: ['<32,b11_b23_b33,b11_b21,w=0.027889>', '<33,b11_b23_b33,b11_b22,w=0.027889>']
  16,ChiouYoungs2008: ['<34,b11_b23_b33,b12_b21,w=0.027889>', '<35,b11_b23_b33,b12_b22,w=0.027889>']
  17,Campbell2003: ['<33,b11_b23_b33,b11_b22,w=0.027889>', '<35,b11_b23_b33,b12_b22,w=0.027889>']
  17,ToroEtAl2002: ['<32,b11_b23_b33,b11_b21,w=0.027889>', '<34,b11_b23_b33,b12_b21,w=0.027889>']>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ======================== =========== ============ ======
source_model     trt_id trt                      num_sources eff_ruptures weight
================ ====== ======================== =========== ============ ======
source_model.xml 0      Active Shallow Crust     1           1,334        1,334 
source_model.xml 1      Stable Continental Crust 1           4,100        102   
source_model.xml 2      Active Shallow Crust     1           1,339        1,339 
source_model.xml 3      Stable Continental Crust 1           5,125        128   
source_model.xml 4      Active Shallow Crust     1           1,344        1,344 
source_model.xml 5      Stable Continental Crust 1           6,150        153   
source_model.xml 6      Active Shallow Crust     1           1,334        1,334 
source_model.xml 7      Stable Continental Crust 1           4,100        102   
source_model.xml 8      Active Shallow Crust     1           1,339        1,339 
source_model.xml 9      Stable Continental Crust 1           5,125        128   
source_model.xml 10     Active Shallow Crust     1           1,344        1,344 
source_model.xml 11     Stable Continental Crust 1           6,150        153   
source_model.xml 12     Active Shallow Crust     1           1,334        1,334 
source_model.xml 13     Stable Continental Crust 1           4,100        102   
source_model.xml 14     Active Shallow Crust     1           1,339        1,339 
source_model.xml 15     Stable Continental Crust 1           5,125        128   
source_model.xml 16     Active Shallow Crust     1           1,344        1,344 
source_model.xml 17     Stable Continental Crust 1           6,150        153   
================ ====== ======================== =========== ============ ======

=============== ======
#TRT models     18    
#sources        18    
#eff_ruptures   58,176
filtered_weight 13,204
=============== ======

Expected data transfer for the sources
--------------------------------------
=========================== ========
Number of tasks to generate 90      
Sent data                   50.05 MB
=========================== ========

Slowest sources
---------------
============ ========= ================= ====== ========= =========== ========== =========
trt_model_id source_id source_class      weight split_num filter_time split_time calc_time
============ ========= ================= ====== ========= =========== ========== =========
16           2         SimpleFaultSource 1,344  1,344     0.003       0.825      0.0      
10           2         SimpleFaultSource 1,344  1,344     0.003       0.758      0.0      
4            2         SimpleFaultSource 1,344  1,344     0.003       0.758      0.0      
2            2         SimpleFaultSource 1,339  1,339     0.003       0.583      0.0      
14           2         SimpleFaultSource 1,339  1,339     0.003       0.582      0.0      
8            2         SimpleFaultSource 1,339  1,339     0.003       0.576      0.0      
0            2         SimpleFaultSource 1,334  1,334     0.003       0.521      0.0      
12           2         SimpleFaultSource 1,334  1,334     0.003       0.496      0.0      
6            2         SimpleFaultSource 1,334  1,334     0.003       0.476      0.0      
1            1         AreaSource        102    1         0.002       0.0        0.0      
9            1         AreaSource        128    1         0.001       0.0        0.0      
3            1         AreaSource        128    1         0.001       0.0        0.0      
17           1         AreaSource        153    1         0.001       0.0        0.0      
11           1         AreaSource        153    1         0.001       0.0        0.0      
5            1         AreaSource        153    1         0.001       0.0        0.0      
13           1         AreaSource        102    1         0.001       0.0        0.0      
7            1         AreaSource        102    1         0.001       0.0        0.0      
15           1         AreaSource        128    1         0.001       0.0        0.0      
============ ========= ================= ====== ========= =========== ========== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
managing sources               8.496     0.0       1     
splitting sources              5.575     0.0       9     
reading composite source model 1.037     0.0       1     
filtering sources              0.039     0.0       18    
total count_eff_ruptures       0.039     0.0       90    
aggregate curves               0.002     0.0       90    
store source_info              4.001E-04 0.0       1     
reading site collection        6.199E-05 0.0       1     
============================== ========= ========= ======