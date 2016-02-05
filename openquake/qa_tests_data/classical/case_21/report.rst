Classical Hazard QA Test, Case 21
=================================

num_sites = 1, sitecol = 684 B

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
concurrent_tasks             16       
sites_per_tile               1000     
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
================ ====== ==================== =========== ============ ============ ======
source_model     trt_id trt                  num_sources num_ruptures eff_ruptures weight
================ ====== ==================== =========== ============ ============ ======
source_model.xml 0      Active Shallow Crust 2           444          444          444.0 
source_model.xml 1      Active Shallow Crust 2           208          208          208.0 
source_model.xml 2      Active Shallow Crust 2           149          149          149.0 
source_model.xml 3      Active Shallow Crust 2           534          534          534.0 
source_model.xml 4      Active Shallow Crust 2           298          298          298.0 
source_model.xml 5      Active Shallow Crust 2           239          239          239.0 
source_model.xml 6      Active Shallow Crust 2           474          474          474.0 
source_model.xml 7      Active Shallow Crust 2           238          238          238.0 
source_model.xml 8      Active Shallow Crust 2           179          179          179.0 
source_model.xml 9      Active Shallow Crust 2           409          409          409.0 
source_model.xml 10     Active Shallow Crust 2           173          173          173.0 
source_model.xml 11     Active Shallow Crust 2           114          114          114.0 
source_model.xml 12     Active Shallow Crust 2           465          465          465.0 
source_model.xml 13     Active Shallow Crust 2           229          229          229.0 
source_model.xml 14     Active Shallow Crust 2           170          170          170.0 
source_model.xml 15     Active Shallow Crust 2           411          411          411.0 
source_model.xml 16     Active Shallow Crust 2           175          175          175.0 
source_model.xml 17     Active Shallow Crust 2           116          116          116.0 
source_model.xml 18     Active Shallow Crust 2           483          483          483.0 
source_model.xml 19     Active Shallow Crust 2           247          247          247.0 
source_model.xml 20     Active Shallow Crust 2           188          188          188.0 
source_model.xml 21     Active Shallow Crust 2           582          582          582.0 
source_model.xml 22     Active Shallow Crust 2           346          346          346.0 
source_model.xml 23     Active Shallow Crust 2           287          287          287.0 
source_model.xml 24     Active Shallow Crust 2           516          516          516.0 
source_model.xml 25     Active Shallow Crust 2           280          280          280.0 
source_model.xml 26     Active Shallow Crust 2           221          221          221.0 
================ ====== ==================== =========== ============ ============ ======

=============== ======
#TRT models     27    
#sources        54    
#tot_ruptures   8175  
#eff_ruptures   8175  
filtered_weight 8175.0
=============== ======

Expected data transfer for the sources
--------------------------------------
=========================== ======
Number of tasks to generate 30    
Sent data                   1.5 MB
=========================== ======

Slowest sources
---------------
============ ========= ================= ====== ========= =========== ========== =========
trt_model_id source_id source_class      weight split_num filter_time split_time calc_time
============ ========= ================= ====== ========= =========== ========== =========
0            SFLT1     SimpleFaultSource 60.0   1         0.001966    0.0        0.0      
2            SFLT2     SimpleFaultSource 89.0   1         0.0016861   0.0        0.0      
12           SFLT2     SimpleFaultSource 384.0  1         0.00168586  0.0        0.0      
16           SFLT1     SimpleFaultSource 27.0   1         0.00167513  0.0        0.0      
21           SFLT1     SimpleFaultSource 198.0  1         0.00166416  0.0        0.0      
17           SFLT1     SimpleFaultSource 27.0   1         0.00166202  0.0        0.0      
17           SFLT2     SimpleFaultSource 89.0   1         0.00166011  0.0        0.0      
15           SFLT1     SimpleFaultSource 27.0   1         0.00165319  0.0        0.0      
14           SFLT1     SimpleFaultSource 81.0   1         0.00164509  0.0        0.0      
18           SFLT1     SimpleFaultSource 99.0   1         0.00163794  0.0        0.0      
1            SFLT2     SimpleFaultSource 148.0  1         0.00163698  0.0        0.0      
3            SFLT1     SimpleFaultSource 150.0  1         0.00163293  0.0        0.0      
7            SFLT2     SimpleFaultSource 148.0  1         0.00163198  0.0        0.0      
5            SFLT1     SimpleFaultSource 150.0  1         0.00163007  0.0        0.0      
4            SFLT1     SimpleFaultSource 150.0  1         0.00162983  0.0        0.0      
14           SFLT2     SimpleFaultSource 89.0   1         0.00162792  0.0        0.0      
6            SFLT1     SimpleFaultSource 90.0   1         0.00162697  0.0        0.0      
22           SFLT1     SimpleFaultSource 198.0  1         0.00162506  0.0        0.0      
20           SFLT2     SimpleFaultSource 89.0   1         0.00162411  0.0        0.0      
19           SFLT1     SimpleFaultSource 99.0   1         0.00162101  0.0        0.0      
============ ========= ================= ====== ========= =========== ========== =========