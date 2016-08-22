Classical Hazard QA Test, Case 21
=================================

gem-tstation:/home/michele/ssd/calc_40707.hdf5 updated Mon Aug 22 12:50:53 2016

num_sites = 1, sitecol = 739 B

Parameters
----------
============================ ================================
calculation_mode             'classical'                     
number_of_logic_tree_samples 0                               
maximum_distance             {u'Active Shallow Crust': 200.0}
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
engine_version               '2.1.0-git8cbb23e'              
============================ ================================

Input files
-----------
======================= ==================================================================================================
Name                    File                                                                                              
======================= ==================================================================================================
gsim_logic_tree         `gsim_logic_tree.xml <gsim_logic_tree.xml>`_                                                      
job_ini                 `job.ini <job.ini>`_                                                                              
source                  `
                        
                     <
                        
                    >`_
source                  `
                        
                     <
                        
                    >`_
source                  `
                        
                     <
                        
                    >`_
source                  `-10.0 <-10.0>`_                                                                                  
source                  `0.0 <0.0>`_                                                                                      
source                  `10.0 <10.0>`_                                                                                    
source                  `30.0 <30.0>`_                                                                                    
source                  `45.0 <45.0>`_                                                                                    
source                  `60.0 <60.0>`_                                                                                    
source                  `source_model.xml <source_model.xml>`_                                                            
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_                                      
======================= ==================================================================================================

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
====== ==================== ============= ============= ==========
grp_id gsims                distances     siteparams    ruptparams
====== ==================== ============= ============= ==========
0      ['SadighEtAl1997()'] set(['rrup']) set(['vs30']) rake mag  
1      ['SadighEtAl1997()'] set(['rrup']) set(['vs30']) rake mag  
2      ['SadighEtAl1997()'] set(['rrup']) set(['vs30']) rake mag  
3      ['SadighEtAl1997()'] set(['rrup']) set(['vs30']) rake mag  
4      ['SadighEtAl1997()'] set(['rrup']) set(['vs30']) rake mag  
5      ['SadighEtAl1997()'] set(['rrup']) set(['vs30']) rake mag  
6      ['SadighEtAl1997()'] set(['rrup']) set(['vs30']) rake mag  
7      ['SadighEtAl1997()'] set(['rrup']) set(['vs30']) rake mag  
8      ['SadighEtAl1997()'] set(['rrup']) set(['vs30']) rake mag  
9      ['SadighEtAl1997()'] set(['rrup']) set(['vs30']) rake mag  
10     ['SadighEtAl1997()'] set(['rrup']) set(['vs30']) rake mag  
11     ['SadighEtAl1997()'] set(['rrup']) set(['vs30']) rake mag  
12     ['SadighEtAl1997()'] set(['rrup']) set(['vs30']) rake mag  
13     ['SadighEtAl1997()'] set(['rrup']) set(['vs30']) rake mag  
14     ['SadighEtAl1997()'] set(['rrup']) set(['vs30']) rake mag  
15     ['SadighEtAl1997()'] set(['rrup']) set(['vs30']) rake mag  
16     ['SadighEtAl1997()'] set(['rrup']) set(['vs30']) rake mag  
17     ['SadighEtAl1997()'] set(['rrup']) set(['vs30']) rake mag  
18     ['SadighEtAl1997()'] set(['rrup']) set(['vs30']) rake mag  
19     ['SadighEtAl1997()'] set(['rrup']) set(['vs30']) rake mag  
20     ['SadighEtAl1997()'] set(['rrup']) set(['vs30']) rake mag  
21     ['SadighEtAl1997()'] set(['rrup']) set(['vs30']) rake mag  
22     ['SadighEtAl1997()'] set(['rrup']) set(['vs30']) rake mag  
23     ['SadighEtAl1997()'] set(['rrup']) set(['vs30']) rake mag  
24     ['SadighEtAl1997()'] set(['rrup']) set(['vs30']) rake mag  
25     ['SadighEtAl1997()'] set(['rrup']) set(['vs30']) rake mag  
26     ['SadighEtAl1997()'] set(['rrup']) set(['vs30']) rake mag  
====== ==================== ============= ============= ==========

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
=============================== ============
classical_max_received_per_task 1,833       
classical_num_tasks             35          
classical_sent.monitor          28,560      
classical_sent.rlzs_by_gsim     19,541      
classical_sent.sitecol          15,155      
classical_sent.sources          45,375      
classical_tot_received          63,761      
hazard.input_weight             8,175       
hazard.n_imts                   1           
hazard.n_levels                 4.000       
hazard.n_realizations           27          
hazard.n_sites                  1           
hazard.n_sources                54          
hazard.output_weight            108         
hostname                        gem-tstation
=============================== ============

Slowest sources
---------------
============ ========= ================= ====== ========= =========== ========== ============= ============= =========
src_group_id source_id source_class      weight split_num filter_time split_time cum_calc_time max_calc_time num_tasks
============ ========= ================= ====== ========= =========== ========== ============= ============= =========
5            SFLT1     SimpleFaultSource 150    1         0.001       0.0        0.820         0.820         1        
4            SFLT1     SimpleFaultSource 150    1         0.001       0.0        0.706         0.706         1        
22           SFLT1     SimpleFaultSource 198    1         0.001       0.0        0.666         0.666         1        
12           SFLT1     SimpleFaultSource 81     1         0.001       0.0        0.666         0.666         1        
21           SFLT1     SimpleFaultSource 198    1         0.001       0.0        0.666         0.666         1        
23           SFLT1     SimpleFaultSource 198    1         0.001       0.0        0.664         0.664         1        
6            SFLT1     SimpleFaultSource 90     1         0.001       0.0        0.625         0.625         1        
3            SFLT1     SimpleFaultSource 150    1         0.001       0.0        0.611         0.611         1        
26           SFLT1     SimpleFaultSource 132    1         0.001       0.0        0.463         0.463         1        
13           SFLT1     SimpleFaultSource 81     1         0.001       0.0        0.453         0.453         1        
25           SFLT1     SimpleFaultSource 132    1         0.001       0.0        0.449         0.449         1        
24           SFLT1     SimpleFaultSource 132    1         0.001       0.0        0.447         0.447         1        
7            SFLT1     SimpleFaultSource 90     1         0.001       0.0        0.443         0.443         1        
14           SFLT1     SimpleFaultSource 81     1         0.001       0.0        0.429         0.429         1        
8            SFLT1     SimpleFaultSource 90     1         0.001       0.0        0.410         0.410         1        
20           SFLT1     SimpleFaultSource 99     1         0.001       0.0        0.383         0.383         1        
2            SFLT1     SimpleFaultSource 60     1         0.001       0.0        0.369         0.369         1        
19           SFLT1     SimpleFaultSource 99     1         0.001       0.0        0.356         0.356         1        
18           SFLT1     SimpleFaultSource 99     1         0.001       0.0        0.356         0.356         1        
0            SFLT1     SimpleFaultSource 60     1         0.002       0.0        0.325         0.325         1        
============ ========= ================= ====== ========= =========== ========== ============= ============= =========

Computation times by source typology
------------------------------------
================= =========== ========== ============= ============= ========= ======
source_class      filter_time split_time cum_calc_time max_calc_time num_tasks counts
================= =========== ========== ============= ============= ========= ======
SimpleFaultSource 0.071       0.0        14            14            54        54    
================= =========== ========== ============= ============= ========= ======

Information about the tasks
---------------------------
=================== ===== ====== ===== ===== =========
measurement         mean  stddev min   max   num_tasks
classical.time_sec  0.407 0.206  0.122 0.859 35       
classical.memory_mb 1.188 1.888  0.0   5.867 35       
=================== ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total classical                14        5.867     35    
making contexts                11        0.0       8,175 
computing poes                 0.939     0.0       8,175 
reading composite source model 0.467     0.0       1     
managing sources               0.139     0.0       1     
filtering sources              0.071     0.0       54    
saving probability maps        0.029     0.0       1     
store source_info              0.017     0.0       1     
read poes                      0.011     0.0       1     
aggregate curves               7.098E-04 0.0       35    
reading site collection        4.911E-05 0.0       1     
============================== ========= ========= ======