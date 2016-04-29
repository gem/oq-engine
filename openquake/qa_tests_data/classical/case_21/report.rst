Classical Hazard QA Test, Case 21
=================================

gem-tstation:/home/michele/ssd/calc_1846.hdf5 updated Fri Apr 29 08:19:06 2016

num_sites = 1, sitecol = 739 B

Parameters
----------
============================ ===================
calculation_mode             'classical'        
number_of_logic_tree_samples 0                  
maximum_distance             {'default': 200.0} 
investigation_time           1.0                
ses_per_logic_tree_path      1                  
truncation_level             3.0                
rupture_mesh_spacing         2.0                
complex_fault_mesh_spacing   2.0                
width_of_mfd_bin             1.0                
area_source_discretization   10.0               
random_seed                  106                
master_seed                  0                  
sites_per_tile               1000               
oqlite_version               '0.13.0-git5086754'
============================ ===================

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
====================== ====== ====================================== =============== ================
smlt_path              weight source_model_file                      gsim_logic_tree num_realizations
====================== ====== ====================================== =============== ================
b1_mfd1_high_dip_dip30 0.013  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
b1_mfd1_high_dip_dip45 0.040  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
b1_mfd1_high_dip_dip60 0.013  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
b1_mfd1_low_dip_dip30  0.013  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
b1_mfd1_low_dip_dip45  0.040  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
b1_mfd1_low_dip_dip60  0.013  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
b1_mfd1_mid_dip_dip30  0.040  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
b1_mfd1_mid_dip_dip45  0.119  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
b1_mfd1_mid_dip_dip60  0.040  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
b1_mfd2_high_dip_dip30 0.014  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
b1_mfd2_high_dip_dip45 0.041  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
b1_mfd2_high_dip_dip60 0.014  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
b1_mfd2_low_dip_dip30  0.014  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
b1_mfd2_low_dip_dip45  0.041  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
b1_mfd2_low_dip_dip60  0.014  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
b1_mfd2_mid_dip_dip30  0.041  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
b1_mfd2_mid_dip_dip45  0.122  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
b1_mfd2_mid_dip_dip60  0.041  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
b1_mfd3_high_dip_dip30 0.013  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
b1_mfd3_high_dip_dip45 0.040  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
b1_mfd3_high_dip_dip60 0.013  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
b1_mfd3_low_dip_dip30  0.013  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
b1_mfd3_low_dip_dip45  0.040  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
b1_mfd3_low_dip_dip60  0.013  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
b1_mfd3_mid_dip_dip30  0.040  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
b1_mfd3_mid_dip_dip45  0.119  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
b1_mfd3_mid_dip_dip60  0.040  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
====================== ====== ====================================== =============== ================

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

  <RlzsAssoc(size=27, rlzs=27)
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
source_model     trt_id trt                  num_sources eff_ruptures weight
================ ====== ==================== =========== ============ ======
source_model.xml 0      Active Shallow Crust 2           444          444   
source_model.xml 1      Active Shallow Crust 2           208          208   
source_model.xml 2      Active Shallow Crust 2           149          149   
source_model.xml 3      Active Shallow Crust 2           534          534   
source_model.xml 4      Active Shallow Crust 2           298          298   
source_model.xml 5      Active Shallow Crust 2           239          239   
source_model.xml 6      Active Shallow Crust 2           474          474   
source_model.xml 7      Active Shallow Crust 2           238          238   
source_model.xml 8      Active Shallow Crust 2           179          179   
source_model.xml 9      Active Shallow Crust 2           409          409   
source_model.xml 10     Active Shallow Crust 2           173          173   
source_model.xml 11     Active Shallow Crust 2           114          114   
source_model.xml 12     Active Shallow Crust 2           465          465   
source_model.xml 13     Active Shallow Crust 2           229          229   
source_model.xml 14     Active Shallow Crust 2           170          170   
source_model.xml 15     Active Shallow Crust 2           411          411   
source_model.xml 16     Active Shallow Crust 2           175          175   
source_model.xml 17     Active Shallow Crust 2           116          116   
source_model.xml 18     Active Shallow Crust 2           483          483   
source_model.xml 19     Active Shallow Crust 2           247          247   
source_model.xml 20     Active Shallow Crust 2           188          188   
source_model.xml 21     Active Shallow Crust 2           582          582   
source_model.xml 22     Active Shallow Crust 2           346          346   
source_model.xml 23     Active Shallow Crust 2           287          287   
source_model.xml 24     Active Shallow Crust 2           516          516   
source_model.xml 25     Active Shallow Crust 2           280          280   
source_model.xml 26     Active Shallow Crust 2           221          221   
================ ====== ==================== =========== ============ ======

=============== =====
#TRT models     27   
#sources        54   
#eff_ruptures   8,175
filtered_weight 8,175
=============== =====

Informational data
------------------
======================================== ==============
count_eff_ruptures_max_received_per_task 2492          
count_eff_ruptures_num_tasks             81            
count_eff_ruptures_sent.monitor          181764        
count_eff_ruptures_sent.rlzs_assoc       3895614       
count_eff_ruptures_sent.sitecol          35397         
count_eff_ruptures_sent.siteidx          405           
count_eff_ruptures_sent.sources          10409382      
count_eff_ruptures_tot_received          201772        
hazard.input_weight                      8175.0        
hazard.n_imts                            1             
hazard.n_levels                          4.0           
hazard.n_realizations                    27            
hazard.n_sites                           1             
hazard.n_sources                         0             
hazard.output_weight                     108.0         
hostname                                 'gem-tstation'
======================================== ==============

Slowest sources
---------------
============ ========= ================= ====== ========= =========== ========== =========
trt_model_id source_id source_class      weight split_num filter_time split_time calc_time
============ ========= ================= ====== ========= =========== ========== =========
0            SFLT2     SimpleFaultSource 384    384       0.004       0.117      0.0      
3            SFLT2     SimpleFaultSource 384    384       0.002       0.066      0.0      
18           SFLT2     SimpleFaultSource 384    384       0.002       0.063      0.0      
6            SFLT2     SimpleFaultSource 384    384       0.002       0.062      0.0      
24           SFLT2     SimpleFaultSource 384    384       0.002       0.062      0.0      
21           SFLT2     SimpleFaultSource 384    384       0.002       0.062      0.0      
9            SFLT2     SimpleFaultSource 384    384       0.002       0.062      0.0      
12           SFLT2     SimpleFaultSource 384    384       0.002       0.062      0.0      
15           SFLT2     SimpleFaultSource 384    384       0.002       0.061      0.0      
0            SFLT1     SimpleFaultSource 60     1         0.002       0.0        0.0      
22           SFLT2     SimpleFaultSource 148    1         0.002       0.0        0.0      
26           SFLT1     SimpleFaultSource 132    1         0.002       0.0        0.0      
26           SFLT2     SimpleFaultSource 89     1         0.002       0.0        0.0      
19           SFLT1     SimpleFaultSource 99     1         0.001       0.0        0.0      
9            SFLT1     SimpleFaultSource 25     1         0.001       0.0        0.0      
1            SFLT2     SimpleFaultSource 148    1         0.001       0.0        0.0      
23           SFLT2     SimpleFaultSource 89     1         0.001       0.0        0.0      
4            SFLT2     SimpleFaultSource 148    1         0.001       0.0        0.0      
6            SFLT1     SimpleFaultSource 90     1         0.001       0.0        0.0      
17           SFLT2     SimpleFaultSource 89     1         0.001       0.0        0.0      
============ ========= ================= ====== ========= =========== ========== =========

Information about the tasks
---------------------------
Not available

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
managing sources               1.364     0.0       1     
splitting sources              0.616     0.0       9     
reading composite source model 0.562     0.0       1     
filtering sources              0.084     0.0       54    
total count_eff_ruptures       0.030     0.004     81    
store source_info              0.005     0.0       1     
aggregate curves               0.002     0.0       81    
reading site collection        3.719E-05 0.0       1     
============================== ========= ========= ======