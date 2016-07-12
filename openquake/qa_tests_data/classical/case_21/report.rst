Classical Hazard QA Test, Case 21
=================================

gem-tstation:/home/michele/ssd/calc_22591.hdf5 updated Tue May 31 15:37:43 2016

num_sites = 1, sitecol = 739 B

Parameters
----------
============================ ===============================
calculation_mode             'classical'                    
number_of_logic_tree_samples 0                              
maximum_distance             {'Active Shallow Crust': 200.0}
investigation_time           1.0                            
ses_per_logic_tree_path      1                              
truncation_level             3.0                            
rupture_mesh_spacing         2.0                            
complex_fault_mesh_spacing   2.0                            
width_of_mfd_bin             1.0                            
area_source_discretization   10.0                           
random_seed                  106                            
master_seed                  0                              
sites_per_tile               10000                          
engine_version               '2.0.0-git4fb4450'             
============================ ===============================

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
====== ================ ========= ========== ==========
grp_id gsims            distances siteparams ruptparams
====== ================ ========= ========== ==========
0      SadighEtAl1997() rrup      vs30       rake mag  
1      SadighEtAl1997() rrup      vs30       rake mag  
2      SadighEtAl1997() rrup      vs30       rake mag  
3      SadighEtAl1997() rrup      vs30       rake mag  
4      SadighEtAl1997() rrup      vs30       rake mag  
5      SadighEtAl1997() rrup      vs30       rake mag  
6      SadighEtAl1997() rrup      vs30       rake mag  
7      SadighEtAl1997() rrup      vs30       rake mag  
8      SadighEtAl1997() rrup      vs30       rake mag  
9      SadighEtAl1997() rrup      vs30       rake mag  
10     SadighEtAl1997() rrup      vs30       rake mag  
11     SadighEtAl1997() rrup      vs30       rake mag  
12     SadighEtAl1997() rrup      vs30       rake mag  
13     SadighEtAl1997() rrup      vs30       rake mag  
14     SadighEtAl1997() rrup      vs30       rake mag  
15     SadighEtAl1997() rrup      vs30       rake mag  
16     SadighEtAl1997() rrup      vs30       rake mag  
17     SadighEtAl1997() rrup      vs30       rake mag  
18     SadighEtAl1997() rrup      vs30       rake mag  
19     SadighEtAl1997() rrup      vs30       rake mag  
20     SadighEtAl1997() rrup      vs30       rake mag  
21     SadighEtAl1997() rrup      vs30       rake mag  
22     SadighEtAl1997() rrup      vs30       rake mag  
23     SadighEtAl1997() rrup      vs30       rake mag  
24     SadighEtAl1997() rrup      vs30       rake mag  
25     SadighEtAl1997() rrup      vs30       rake mag  
26     SadighEtAl1997() rrup      vs30       rake mag  
====== ================ ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=27, rlzs=27)
  0,SadighEtAl1997(): ['<0,b1_mfd1_high_dip_dip30~Sad1997,w=0.0131999998793>']
  1,SadighEtAl1997(): ['<1,b1_mfd1_high_dip_dip45~Sad1997,w=0.0395999996379>']
  2,SadighEtAl1997(): ['<2,b1_mfd1_high_dip_dip60~Sad1997,w=0.0131999998793>']
  3,SadighEtAl1997(): ['<3,b1_mfd1_low_dip_dip30~Sad1997,w=0.0131999998793>']
  4,SadighEtAl1997(): ['<4,b1_mfd1_low_dip_dip45~Sad1997,w=0.0395999996379>']
  5,SadighEtAl1997(): ['<5,b1_mfd1_low_dip_dip60~Sad1997,w=0.0131999998793>']
  6,SadighEtAl1997(): ['<6,b1_mfd1_mid_dip_dip30~Sad1997,w=0.0395999996379>']
  7,SadighEtAl1997(): ['<7,b1_mfd1_mid_dip_dip45~Sad1997,w=0.118799998914>']
  8,SadighEtAl1997(): ['<8,b1_mfd1_mid_dip_dip60~Sad1997,w=0.0395999996379>']
  9,SadighEtAl1997(): ['<9,b1_mfd2_high_dip_dip30~Sad1997,w=0.0136000001296>']
  10,SadighEtAl1997(): ['<10,b1_mfd2_high_dip_dip45~Sad1997,w=0.0408000013202>']
  11,SadighEtAl1997(): ['<11,b1_mfd2_high_dip_dip60~Sad1997,w=0.0136000001296>']
  12,SadighEtAl1997(): ['<12,b1_mfd2_low_dip_dip30~Sad1997,w=0.0136000001296>']
  13,SadighEtAl1997(): ['<13,b1_mfd2_low_dip_dip45~Sad1997,w=0.0408000013202>']
  14,SadighEtAl1997(): ['<14,b1_mfd2_low_dip_dip60~Sad1997,w=0.0136000001296>']
  15,SadighEtAl1997(): ['<15,b1_mfd2_mid_dip_dip30~Sad1997,w=0.0408000013202>']
  16,SadighEtAl1997(): ['<16,b1_mfd2_mid_dip_dip45~Sad1997,w=0.122400000235>']
  17,SadighEtAl1997(): ['<17,b1_mfd2_mid_dip_dip60~Sad1997,w=0.0408000013202>']
  18,SadighEtAl1997(): ['<18,b1_mfd3_high_dip_dip30~Sad1997,w=0.0131999998793>']
  19,SadighEtAl1997(): ['<19,b1_mfd3_high_dip_dip45~Sad1997,w=0.0395999996379>']
  20,SadighEtAl1997(): ['<20,b1_mfd3_high_dip_dip60~Sad1997,w=0.0131999998793>']
  21,SadighEtAl1997(): ['<21,b1_mfd3_low_dip_dip30~Sad1997,w=0.0131999998793>']
  22,SadighEtAl1997(): ['<22,b1_mfd3_low_dip_dip45~Sad1997,w=0.0395999996379>']
  23,SadighEtAl1997(): ['<23,b1_mfd3_low_dip_dip60~Sad1997,w=0.0131999998793>']
  24,SadighEtAl1997(): ['<24,b1_mfd3_mid_dip_dip30~Sad1997,w=0.0395999996379>']
  25,SadighEtAl1997(): ['<25,b1_mfd3_mid_dip_dip45~Sad1997,w=0.118799998914>']
  26,SadighEtAl1997(): ['<26,b1_mfd3_mid_dip_dip60~Sad1997,w=0.0395999996379>']>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== =========== ============ ======
source_model     grp_id trt                  num_sources eff_ruptures weight
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
======================================== ============
count_eff_ruptures_max_received_per_task 2,514       
count_eff_ruptures_num_tasks             46          
count_eff_ruptures_sent.monitor          103,638     
count_eff_ruptures_sent.rlzs_assoc       265,742     
count_eff_ruptures_sent.sitecol          19,918      
count_eff_ruptures_sent.siteidx          230         
count_eff_ruptures_sent.sources          53,461      
count_eff_ruptures_tot_received          115,607     
hazard.input_weight                      8,175       
hazard.n_imts                            1           
hazard.n_levels                          4.000       
hazard.n_realizations                    27          
hazard.n_sites                           1           
hazard.n_sources                         0           
hazard.output_weight                     108         
hostname                                 gem-tstation
======================================== ============

Slowest sources
---------------
============ ========= ================= ====== ========= =========== ========== =========
src_group_id source_id source_class      weight split_num filter_time split_time calc_time
============ ========= ================= ====== ========= =========== ========== =========
0            SFLT1     SimpleFaultSource 60     1         0.002       0.0        0.0      
5            SFLT1     SimpleFaultSource 150    1         0.001       0.0        0.0      
0            SFLT2     SimpleFaultSource 384    1         0.001       0.0        0.0      
9            SFLT2     SimpleFaultSource 384    1         0.001       0.0        0.0      
3            SFLT2     SimpleFaultSource 384    1         0.001       0.0        0.0      
8            SFLT1     SimpleFaultSource 90     1         0.001       0.0        0.0      
6            SFLT2     SimpleFaultSource 384    1         0.001       0.0        0.0      
11           SFLT1     SimpleFaultSource 25     1         0.001       0.0        0.0      
2            SFLT1     SimpleFaultSource 60     1         0.001       0.0        0.0      
5            SFLT2     SimpleFaultSource 89     1         0.001       0.0        0.0      
1            SFLT2     SimpleFaultSource 148    1         0.001       0.0        0.0      
2            SFLT2     SimpleFaultSource 89     1         0.001       0.0        0.0      
9            SFLT1     SimpleFaultSource 25     1         0.001       0.0        0.0      
7            SFLT1     SimpleFaultSource 90     1         0.001       0.0        0.0      
4            SFLT2     SimpleFaultSource 148    1         0.001       0.0        0.0      
1            SFLT1     SimpleFaultSource 60     1         0.001       0.0        0.0      
7            SFLT2     SimpleFaultSource 148    1         0.001       0.0        0.0      
4            SFLT1     SimpleFaultSource 150    1         0.001       0.0        0.0      
6            SFLT1     SimpleFaultSource 90     1         0.001       0.0        0.0      
10           SFLT1     SimpleFaultSource 25     1         0.001       0.0        0.0      
============ ========= ================= ====== ========= =========== ========== =========

Computation times by source typology
------------------------------------
================= =========== ========== ========= ======
source_class      filter_time split_time calc_time counts
================= =========== ========== ========= ======
SimpleFaultSource 0.069       0.0        0.0       54    
================= =========== ========== ========= ======

Information about the tasks
---------------------------
Not available

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
reading composite source model 0.399     0.0       1     
managing sources               0.142     0.0       1     
filtering sources              0.069     0.0       54    
total count_eff_ruptures       0.011     0.0       46    
store source_info              0.004     0.0       1     
aggregate curves               6.509E-04 0.0       46    
reading site collection        3.099E-05 0.0       1     
============================== ========= ========= ======