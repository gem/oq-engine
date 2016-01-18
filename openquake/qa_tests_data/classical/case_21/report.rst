Classical Hazard QA Test, Case 21
=================================

num_sites = 1, sitecol = 437 B

Parameters
----------
============================ =========
calculation_mode             classical
number_of_logic_tree_samples 0        
maximum_distance             200.0    
investigation_time           1.0      
ses_per_logic_tree_path      1        
truncation_level             3.0      
rupture_mesh_spacing         2.0      
complex_fault_mesh_spacing   2.0      
width_of_mfd_bin             1.0      
area_source_discretization   10.0     
random_seed                  106      
master_seed                  0        
concurrent_tasks             64       
============================ =========

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gsim_logic_tree.xml <gsim_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
source                  `source_model.xml <source_model.xml>`_                      
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
====================== ======== ====================================== =============== ================
smlt_path              weight   source_model_file                      gsim_logic_tree num_realizations
====================== ======== ====================================== =============== ================
b1_mfd1_high_dip_dip30 0.013200 `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
b1_mfd1_high_dip_dip45 0.039600 `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
b1_mfd1_high_dip_dip60 0.013200 `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
b1_mfd1_low_dip_dip30  0.013200 `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
b1_mfd1_low_dip_dip45  0.039600 `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
b1_mfd1_low_dip_dip60  0.013200 `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
b1_mfd1_mid_dip_dip30  0.039600 `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
b1_mfd1_mid_dip_dip45  0.118800 `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
b1_mfd1_mid_dip_dip60  0.039600 `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
b1_mfd2_high_dip_dip30 0.013600 `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
b1_mfd2_high_dip_dip45 0.040800 `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
b1_mfd2_high_dip_dip60 0.013600 `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
b1_mfd2_low_dip_dip30  0.013600 `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
b1_mfd2_low_dip_dip45  0.040800 `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
b1_mfd2_low_dip_dip60  0.013600 `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
b1_mfd2_mid_dip_dip30  0.040800 `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
b1_mfd2_mid_dip_dip45  0.122400 `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
b1_mfd2_mid_dip_dip60  0.040800 `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
b1_mfd3_high_dip_dip30 0.013200 `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
b1_mfd3_high_dip_dip45 0.039600 `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
b1_mfd3_high_dip_dip60 0.013200 `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
b1_mfd3_low_dip_dip30  0.013200 `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
b1_mfd3_low_dip_dip45  0.039600 `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
b1_mfd3_low_dip_dip60  0.013200 `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
b1_mfd3_mid_dip_dip30  0.039600 `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
b1_mfd3_mid_dip_dip45  0.118800 `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
b1_mfd3_mid_dip_dip60  0.039600 `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
====================== ======== ====================================== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ============== ========= ========== ==========
trt_id gsims          distances siteparams ruptparams
====== ============== ========= ========== ==========
0      SadighEtAl1997 rrup      vs30       rake mag  
1      SadighEtAl1997 rrup      vs30       rake mag  
2      SadighEtAl1997 rrup      vs30       rake mag  
3      SadighEtAl1997 rrup      vs30       rake mag  
4      SadighEtAl1997 rrup      vs30       rake mag  
5      SadighEtAl1997 rrup      vs30       rake mag  
6      SadighEtAl1997 rrup      vs30       rake mag  
7      SadighEtAl1997 rrup      vs30       rake mag  
8      SadighEtAl1997 rrup      vs30       rake mag  
9      SadighEtAl1997 rrup      vs30       rake mag  
10     SadighEtAl1997 rrup      vs30       rake mag  
11     SadighEtAl1997 rrup      vs30       rake mag  
12     SadighEtAl1997 rrup      vs30       rake mag  
13     SadighEtAl1997 rrup      vs30       rake mag  
14     SadighEtAl1997 rrup      vs30       rake mag  
15     SadighEtAl1997 rrup      vs30       rake mag  
16     SadighEtAl1997 rrup      vs30       rake mag  
17     SadighEtAl1997 rrup      vs30       rake mag  
18     SadighEtAl1997 rrup      vs30       rake mag  
19     SadighEtAl1997 rrup      vs30       rake mag  
20     SadighEtAl1997 rrup      vs30       rake mag  
21     SadighEtAl1997 rrup      vs30       rake mag  
22     SadighEtAl1997 rrup      vs30       rake mag  
23     SadighEtAl1997 rrup      vs30       rake mag  
24     SadighEtAl1997 rrup      vs30       rake mag  
25     SadighEtAl1997 rrup      vs30       rake mag  
26     SadighEtAl1997 rrup      vs30       rake mag  
====== ============== ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(27)
  0,SadighEtAl1997: ['<0,b1_mfd1_high_dip_dip30,Sad1997,w=0.0132>']
  1,SadighEtAl1997: ['<1,b1_mfd1_high_dip_dip45,Sad1997,w=0.0396>']
  2,SadighEtAl1997: ['<2,b1_mfd1_high_dip_dip60,Sad1997,w=0.0132>']
  3,SadighEtAl1997: ['<3,b1_mfd1_low_dip_dip30,Sad1997,w=0.0132>']
  4,SadighEtAl1997: ['<4,b1_mfd1_low_dip_dip45,Sad1997,w=0.0396>']
  5,SadighEtAl1997: ['<5,b1_mfd1_low_dip_dip60,Sad1997,w=0.0132>']
  6,SadighEtAl1997: ['<6,b1_mfd1_mid_dip_dip30,Sad1997,w=0.0396>']
  7,SadighEtAl1997: ['<7,b1_mfd1_mid_dip_dip45,Sad1997,w=0.1188>']
  8,SadighEtAl1997: ['<8,b1_mfd1_mid_dip_dip60,Sad1997,w=0.0396>']
  9,SadighEtAl1997: ['<9,b1_mfd2_high_dip_dip30,Sad1997,w=0.0136>']
  10,SadighEtAl1997: ['<10,b1_mfd2_high_dip_dip45,Sad1997,w=0.0408>']
  11,SadighEtAl1997: ['<11,b1_mfd2_high_dip_dip60,Sad1997,w=0.0136>']
  12,SadighEtAl1997: ['<12,b1_mfd2_low_dip_dip30,Sad1997,w=0.0136>']
  13,SadighEtAl1997: ['<13,b1_mfd2_low_dip_dip45,Sad1997,w=0.0408>']
  14,SadighEtAl1997: ['<14,b1_mfd2_low_dip_dip60,Sad1997,w=0.0136>']
  15,SadighEtAl1997: ['<15,b1_mfd2_mid_dip_dip30,Sad1997,w=0.0408>']
  16,SadighEtAl1997: ['<16,b1_mfd2_mid_dip_dip45,Sad1997,w=0.1224>']
  17,SadighEtAl1997: ['<17,b1_mfd2_mid_dip_dip60,Sad1997,w=0.0408>']
  18,SadighEtAl1997: ['<18,b1_mfd3_high_dip_dip30,Sad1997,w=0.0132>']
  19,SadighEtAl1997: ['<19,b1_mfd3_high_dip_dip45,Sad1997,w=0.0396>']
  20,SadighEtAl1997: ['<20,b1_mfd3_high_dip_dip60,Sad1997,w=0.0132>']
  21,SadighEtAl1997: ['<21,b1_mfd3_low_dip_dip30,Sad1997,w=0.0132>']
  22,SadighEtAl1997: ['<22,b1_mfd3_low_dip_dip45,Sad1997,w=0.0396>']
  23,SadighEtAl1997: ['<23,b1_mfd3_low_dip_dip60,Sad1997,w=0.0132>']
  24,SadighEtAl1997: ['<24,b1_mfd3_mid_dip_dip30,Sad1997,w=0.0396>']
  25,SadighEtAl1997: ['<25,b1_mfd3_mid_dip_dip45,Sad1997,w=0.1188>']
  26,SadighEtAl1997: ['<26,b1_mfd3_mid_dip_dip60,Sad1997,w=0.0396>']>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== =========== ============ ======
source_model     trt_id trt                  num_sources num_ruptures weight
================ ====== ==================== =========== ============ ======
source_model.xml 0      Active Shallow Crust 444         444          444.0 
source_model.xml 1      Active Shallow Crust 208         208          208.0 
source_model.xml 2      Active Shallow Crust 149         149          149.0 
source_model.xml 3      Active Shallow Crust 534         534          534.0 
source_model.xml 4      Active Shallow Crust 298         298          298.0 
source_model.xml 5      Active Shallow Crust 239         239          239.0 
source_model.xml 6      Active Shallow Crust 474         474          474.0 
source_model.xml 7      Active Shallow Crust 238         238          238.0 
source_model.xml 8      Active Shallow Crust 179         179          179.0 
source_model.xml 9      Active Shallow Crust 409         409          409.0 
source_model.xml 10     Active Shallow Crust 173         173          173.0 
source_model.xml 11     Active Shallow Crust 114         114          114.0 
source_model.xml 12     Active Shallow Crust 465         465          465.0 
source_model.xml 13     Active Shallow Crust 229         229          229.0 
source_model.xml 14     Active Shallow Crust 170         170          170.0 
source_model.xml 15     Active Shallow Crust 411         411          411.0 
source_model.xml 16     Active Shallow Crust 175         175          175.0 
source_model.xml 17     Active Shallow Crust 116         116          116.0 
source_model.xml 18     Active Shallow Crust 483         483          483.0 
source_model.xml 19     Active Shallow Crust 247         247          247.0 
source_model.xml 20     Active Shallow Crust 188         188          188.0 
source_model.xml 21     Active Shallow Crust 582         582          582.0 
source_model.xml 22     Active Shallow Crust 346         346          346.0 
source_model.xml 23     Active Shallow Crust 287         287          287.0 
source_model.xml 24     Active Shallow Crust 516         516          516.0 
source_model.xml 25     Active Shallow Crust 280         280          280.0 
source_model.xml 26     Active Shallow Crust 221         221          221.0 
================ ====== ==================== =========== ============ ======

=============== ======
#TRT models     27    
#sources        54    
#ruptures       8175  
filtered_weight 8175.0
=============== ======

Expected data transfer for the sources
--------------------------------------
=========================== =========
Number of tasks to generate 81       
Sent data                   18.4 MB  
Total received data         124.27 KB
Maximum received per task   1.53 KB  
=========================== =========