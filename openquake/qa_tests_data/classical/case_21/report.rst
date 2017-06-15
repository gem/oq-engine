Classical Hazard QA Test, Case 21
=================================

================================================ ========================
tstation.gem.lan:/mnt/ssd/oqdata/calc_29227.hdf5 Wed Jun 14 10:04:20 2017
engine_version                                   2.5.0-gite200a20        
================================================ ========================

num_sites = 1, num_imts = 1

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
#tot_weight   0    
============= =====

Informational data
------------------
============================== =====================================================================================
count_eff_ruptures.received    tot 31.52 KB, max_per_task 605 B                                                     
count_eff_ruptures.sent        sources 60.27 KB, srcfilter 36.74 KB, param 32.87 KB, monitor 16.81 KB, gsims 4.89 KB
hazard.input_weight            8,175                                                                                
hazard.n_imts                  1 B                                                                                  
hazard.n_levels                4 B                                                                                  
hazard.n_realizations          27 B                                                                                 
hazard.n_sites                 1 B                                                                                  
hazard.n_sources               54 B                                                                                 
hazard.output_weight           4.000                                                                                
hostname                       tstation.gem.lan                                                                     
require_epsilons               0 B                                                                                  
============================== =====================================================================================

Slowest sources
---------------
====== ========= ================= ============ ========= ========= =========
grp_id source_id source_class      num_ruptures calc_time num_sites num_split
====== ========= ================= ============ ========= ========= =========
0      SFLT2     SimpleFaultSource 384          0.005     1         2        
3      SFLT2     SimpleFaultSource 384          0.005     1         2        
12     SFLT2     SimpleFaultSource 384          0.004     1         2        
6      SFLT2     SimpleFaultSource 384          0.004     1         2        
18     SFLT2     SimpleFaultSource 384          0.004     1         2        
21     SFLT2     SimpleFaultSource 384          0.004     1         2        
24     SFLT2     SimpleFaultSource 384          0.004     1         2        
15     SFLT2     SimpleFaultSource 384          0.003     1         2        
9      SFLT2     SimpleFaultSource 384          0.003     1         2        
2      SFLT1     SimpleFaultSource 60           0.003     1         1        
1      SFLT1     SimpleFaultSource 60           0.003     1         1        
3      SFLT1     SimpleFaultSource 150          0.003     1         1        
12     SFLT1     SimpleFaultSource 81           0.002     1         1        
16     SFLT1     SimpleFaultSource 27           0.002     1         1        
15     SFLT1     SimpleFaultSource 27           0.002     1         1        
10     SFLT1     SimpleFaultSource 25           0.002     1         1        
20     SFLT2     SimpleFaultSource 89           0.002     1         1        
16     SFLT2     SimpleFaultSource 148          0.002     1         1        
26     SFLT1     SimpleFaultSource 132          0.002     1         1        
2      SFLT2     SimpleFaultSource 89           0.002     1         1        
====== ========= ================= ============ ========= ========= =========

Computation times by source typology
------------------------------------
================= ========= ======
source_class      calc_time counts
================= ========= ======
SimpleFaultSource 0.118     54    
================= ========= ======

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
count_eff_ruptures 0.003 0.001  0.001 0.006 55       
================== ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
reading composite source model 0.378     0.0       1     
managing sources               0.289     0.0       1     
total count_eff_ruptures       0.152     0.0       55    
prefiltering source model      0.051     0.0       1     
store source_info              0.008     0.0       1     
aggregate curves               0.001     0.0       55    
reading site collection        4.506E-05 0.0       1     
saving probability maps        3.386E-05 0.0       1     
============================== ========= ========= ======