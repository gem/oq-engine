Classical Hazard QA Test, Case 21
=================================

============================================ ========================
gem-tstation:/mnt/ssd/oqdata/calc_85560.hdf5 Tue Feb 14 15:40:09 2017
engine_version                               2.3.0-git1f56df2        
hazardlib_version                            0.23.0-git6937706       
============================================ ========================

num_sites = 1, sitecol = 809 B

Parameters
----------
=============================== ==================
calculation_mode                'classical'       
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              1.0               
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                1.0               
area_source_discretization      10.0              
ground_motion_correlation_model None              
random_seed                     106               
master_seed                     0                 
=============================== ==================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gsim_logic_tree.xml <gsim_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
source                  `-10.0 <-10.0>`_                                            
source                  `0.0 <0.0>`_                                                
source                  `10.0 <10.0>`_                                              
source                  `30.0 <30.0>`_                                              
source                  `45.0 <45.0>`_                                              
source                  `60.0 <60.0>`_                                              
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
0      SadighEtAl1997() rrup      vs30       mag rake  
1      SadighEtAl1997() rrup      vs30       mag rake  
2      SadighEtAl1997() rrup      vs30       mag rake  
3      SadighEtAl1997() rrup      vs30       mag rake  
4      SadighEtAl1997() rrup      vs30       mag rake  
5      SadighEtAl1997() rrup      vs30       mag rake  
6      SadighEtAl1997() rrup      vs30       mag rake  
7      SadighEtAl1997() rrup      vs30       mag rake  
8      SadighEtAl1997() rrup      vs30       mag rake  
9      SadighEtAl1997() rrup      vs30       mag rake  
10     SadighEtAl1997() rrup      vs30       mag rake  
11     SadighEtAl1997() rrup      vs30       mag rake  
12     SadighEtAl1997() rrup      vs30       mag rake  
13     SadighEtAl1997() rrup      vs30       mag rake  
14     SadighEtAl1997() rrup      vs30       mag rake  
15     SadighEtAl1997() rrup      vs30       mag rake  
16     SadighEtAl1997() rrup      vs30       mag rake  
17     SadighEtAl1997() rrup      vs30       mag rake  
18     SadighEtAl1997() rrup      vs30       mag rake  
19     SadighEtAl1997() rrup      vs30       mag rake  
20     SadighEtAl1997() rrup      vs30       mag rake  
21     SadighEtAl1997() rrup      vs30       mag rake  
22     SadighEtAl1997() rrup      vs30       mag rake  
23     SadighEtAl1997() rrup      vs30       mag rake  
24     SadighEtAl1997() rrup      vs30       mag rake  
25     SadighEtAl1997() rrup      vs30       mag rake  
26     SadighEtAl1997() rrup      vs30       mag rake  
====== ================ ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=27, rlzs=27)
  0,SadighEtAl1997(): ['<0,b1_mfd1_high_dip_dip30~Sad1997,w=0.013199999928474426>']
  1,SadighEtAl1997(): ['<1,b1_mfd1_high_dip_dip45~Sad1997,w=0.03959999978542328>']
  2,SadighEtAl1997(): ['<2,b1_mfd1_high_dip_dip60~Sad1997,w=0.013199999928474426>']
  3,SadighEtAl1997(): ['<3,b1_mfd1_low_dip_dip30~Sad1997,w=0.013199999928474426>']
  4,SadighEtAl1997(): ['<4,b1_mfd1_low_dip_dip45~Sad1997,w=0.03959999978542328>']
  5,SadighEtAl1997(): ['<5,b1_mfd1_low_dip_dip60~Sad1997,w=0.013199999928474426>']
  6,SadighEtAl1997(): ['<6,b1_mfd1_mid_dip_dip30~Sad1997,w=0.03959999978542328>']
  7,SadighEtAl1997(): ['<7,b1_mfd1_mid_dip_dip45~Sad1997,w=0.11879999935626984>']
  8,SadighEtAl1997(): ['<8,b1_mfd1_mid_dip_dip60~Sad1997,w=0.03959999978542328>']
  9,SadighEtAl1997(): ['<9,b1_mfd2_high_dip_dip30~Sad1997,w=0.01360000018030405>']
  10,SadighEtAl1997(): ['<10,b1_mfd2_high_dip_dip45~Sad1997,w=0.040800001472234726>']
  11,SadighEtAl1997(): ['<11,b1_mfd2_high_dip_dip60~Sad1997,w=0.01360000018030405>']
  12,SadighEtAl1997(): ['<12,b1_mfd2_low_dip_dip30~Sad1997,w=0.01360000018030405>']
  13,SadighEtAl1997(): ['<13,b1_mfd2_low_dip_dip45~Sad1997,w=0.040800001472234726>']
  14,SadighEtAl1997(): ['<14,b1_mfd2_low_dip_dip60~Sad1997,w=0.01360000018030405>']
  15,SadighEtAl1997(): ['<15,b1_mfd2_mid_dip_dip30~Sad1997,w=0.040800001472234726>']
  16,SadighEtAl1997(): ['<16,b1_mfd2_mid_dip_dip45~Sad1997,w=0.12240000069141388>']
  17,SadighEtAl1997(): ['<17,b1_mfd2_mid_dip_dip60~Sad1997,w=0.040800001472234726>']
  18,SadighEtAl1997(): ['<18,b1_mfd3_high_dip_dip30~Sad1997,w=0.013199999928474426>']
  19,SadighEtAl1997(): ['<19,b1_mfd3_high_dip_dip45~Sad1997,w=0.03959999978542328>']
  20,SadighEtAl1997(): ['<20,b1_mfd3_high_dip_dip60~Sad1997,w=0.013199999928474426>']
  21,SadighEtAl1997(): ['<21,b1_mfd3_low_dip_dip30~Sad1997,w=0.013199999928474426>']
  22,SadighEtAl1997(): ['<22,b1_mfd3_low_dip_dip45~Sad1997,w=0.03959999978542328>']
  23,SadighEtAl1997(): ['<23,b1_mfd3_low_dip_dip60~Sad1997,w=0.013199999928474426>']
  24,SadighEtAl1997(): ['<24,b1_mfd3_mid_dip_dip30~Sad1997,w=0.03959999978542328>']
  25,SadighEtAl1997(): ['<25,b1_mfd3_mid_dip_dip45~Sad1997,w=0.11879999935626984>']
  26,SadighEtAl1997(): ['<26,b1_mfd3_mid_dip_dip60~Sad1997,w=0.03959999978542328>']>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== =========== ============ ============
source_model     grp_id trt                  num_sources eff_ruptures tot_ruptures
================ ====== ==================== =========== ============ ============
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
================ ====== ==================== =========== ============ ============

============= =====
#TRT models   27   
#sources      54   
#eff_ruptures 8,175
#tot_ruptures 8,175
#tot_weight   8,175
============= =====

Informational data
------------------
=========================================== ============
count_eff_ruptures_max_received_per_task    1,288       
count_eff_ruptures_num_tasks                55          
count_eff_ruptures_sent.gsims               5,005       
count_eff_ruptures_sent.monitor             58,465      
count_eff_ruptures_sent.sources             61,719      
count_eff_ruptures_sent.srcfilter           39,050      
count_eff_ruptures_tot_received             70,696      
hazard.input_weight                         8,175       
hazard.n_imts                               1           
hazard.n_levels                             4           
hazard.n_realizations                       27          
hazard.n_sites                              1           
hazard.n_sources                            54          
hazard.output_weight                        108         
hostname                                    gem-tstation
require_epsilons                            False       
=========================================== ============

Slowest sources
---------------
====== ========= ================= ============ ========= ========= =========
grp_id source_id source_class      num_ruptures calc_time num_sites num_split
====== ========= ================= ============ ========= ========= =========
3      SFLT2     SimpleFaultSource 384          0.0       1         0        
15     SFLT1     SimpleFaultSource 27           0.0       1         0        
8      SFLT1     SimpleFaultSource 90           0.0       1         0        
13     SFLT1     SimpleFaultSource 81           0.0       1         0        
22     SFLT1     SimpleFaultSource 198          0.0       1         0        
18     SFLT2     SimpleFaultSource 384          0.0       1         0        
5      SFLT1     SimpleFaultSource 150          0.0       1         0        
14     SFLT1     SimpleFaultSource 81           0.0       1         0        
1      SFLT2     SimpleFaultSource 148          0.0       1         0        
10     SFLT2     SimpleFaultSource 148          0.0       1         0        
19     SFLT2     SimpleFaultSource 148          0.0       1         0        
24     SFLT1     SimpleFaultSource 132          0.0       1         0        
21     SFLT1     SimpleFaultSource 198          0.0       1         0        
17     SFLT2     SimpleFaultSource 89           0.0       1         0        
26     SFLT2     SimpleFaultSource 89           0.0       1         0        
7      SFLT2     SimpleFaultSource 148          0.0       1         0        
0      SFLT2     SimpleFaultSource 384          0.0       1         0        
9      SFLT2     SimpleFaultSource 384          0.0       1         0        
12     SFLT1     SimpleFaultSource 81           0.0       1         0        
4      SFLT1     SimpleFaultSource 150          0.0       1         0        
====== ========= ================= ============ ========= ========= =========

Computation times by source typology
------------------------------------
================= ========= ======
source_class      calc_time counts
================= ========= ======
SimpleFaultSource 0.0       54    
================= ========= ======

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
count_eff_ruptures 0.220 0.221  0.019 0.705 55       
================== ===== ====== ===== ===== =========

Slowest operations
------------------
================================ ========= ========= ======
operation                        time_sec  memory_mb counts
================================ ========= ========= ======
total count_eff_ruptures         12        4.230     55    
reading composite source model   0.327     0.0       1     
managing sources                 0.231     0.0       1     
filtering composite source model 0.049     0.0       1     
store source_info                0.001     0.0       1     
aggregate curves                 8.376E-04 0.0       55    
reading site collection          5.388E-05 0.0       1     
saving probability maps          3.862E-05 0.0       1     
================================ ========= ========= ======