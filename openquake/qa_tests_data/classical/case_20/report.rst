Classical Hazard QA Test, Case 20
=================================

============================================== ========================
gem-tstation:/home/michele/ssd/calc_66986.hdf5 Wed Nov  9 08:15:23 2016
engine_version                                 2.2.0-git54d01f4        
hazardlib_version                              0.22.0-git173c60c       
============================================== ========================

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
============================ ================================

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
========================= ====== ====================================== =============== ================
smlt_path                 weight source_model_file                      gsim_logic_tree num_realizations
========================= ====== ====================================== =============== ================
sm1_sg1_cog1_char_complex 0.070  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
sm1_sg1_cog1_char_plane   0.105  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
sm1_sg1_cog1_char_simple  0.175  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
sm1_sg1_cog2_char_complex 0.070  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
sm1_sg1_cog2_char_plane   0.105  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
sm1_sg1_cog2_char_simple  0.175  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
sm1_sg2_cog1_char_complex 0.030  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
sm1_sg2_cog1_char_plane   0.045  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
sm1_sg2_cog1_char_simple  0.075  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
sm1_sg2_cog2_char_complex 0.030  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
sm1_sg2_cog2_char_plane   0.045  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
sm1_sg2_cog2_char_simple  0.075  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
========================= ====== ====================================== =============== ================

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
====== ================ ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=12, rlzs=12)
  0,SadighEtAl1997(): ['<0,sm1_sg1_cog1_char_complex~Sad1997,w=0.070000000298>']
  1,SadighEtAl1997(): ['<1,sm1_sg1_cog1_char_plane~Sad1997,w=0.104999996722>']
  2,SadighEtAl1997(): ['<2,sm1_sg1_cog1_char_simple~Sad1997,w=0.17499999702>']
  3,SadighEtAl1997(): ['<3,sm1_sg1_cog2_char_complex~Sad1997,w=0.070000000298>']
  4,SadighEtAl1997(): ['<4,sm1_sg1_cog2_char_plane~Sad1997,w=0.104999996722>']
  5,SadighEtAl1997(): ['<5,sm1_sg1_cog2_char_simple~Sad1997,w=0.17499999702>']
  6,SadighEtAl1997(): ['<6,sm1_sg2_cog1_char_complex~Sad1997,w=0.0299999993294>']
  7,SadighEtAl1997(): ['<7,sm1_sg2_cog1_char_plane~Sad1997,w=0.0450000017881>']
  8,SadighEtAl1997(): ['<8,sm1_sg2_cog1_char_simple~Sad1997,w=0.0750000029802>']
  9,SadighEtAl1997(): ['<9,sm1_sg2_cog2_char_complex~Sad1997,w=0.0299999993294>']
  10,SadighEtAl1997(): ['<10,sm1_sg2_cog2_char_plane~Sad1997,w=0.0450000017881>']
  11,SadighEtAl1997(): ['<11,sm1_sg2_cog2_char_simple~Sad1997,w=0.0750000029802>']>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== =========== ============ ============
source_model     grp_id trt                  num_sources eff_ruptures tot_ruptures
================ ====== ==================== =========== ============ ============
source_model.xml 0      Active Shallow Crust 3           86           86          
source_model.xml 1      Active Shallow Crust 3           86           86          
source_model.xml 2      Active Shallow Crust 3           86           86          
source_model.xml 3      Active Shallow Crust 3           119          119         
source_model.xml 4      Active Shallow Crust 3           119          119         
source_model.xml 5      Active Shallow Crust 3           119          119         
source_model.xml 6      Active Shallow Crust 3           88           88          
source_model.xml 7      Active Shallow Crust 3           88           88          
source_model.xml 8      Active Shallow Crust 3           88           88          
source_model.xml 9      Active Shallow Crust 3           121          121         
source_model.xml 10     Active Shallow Crust 3           121          121         
source_model.xml 11     Active Shallow Crust 3           121          121         
================ ====== ==================== =========== ============ ============

============= =====
#TRT models   12   
#sources      36   
#eff_ruptures 1,242
#tot_ruptures 1,242
#tot_weight   1,788
============= =====

Informational data
------------------
======================================== ============
count_eff_ruptures_max_received_per_task 1,262       
count_eff_ruptures_num_tasks             12          
count_eff_ruptures_sent.gsims            984         
count_eff_ruptures_sent.monitor          12,276      
count_eff_ruptures_sent.sitecol          5,196       
count_eff_ruptures_sent.sources          95,160      
count_eff_ruptures_tot_received          15,144      
hazard.input_weight                      1,788       
hazard.n_imts                            1           
hazard.n_levels                          4           
hazard.n_realizations                    12          
hazard.n_sites                           1           
hazard.n_sources                         36          
hazard.output_weight                     48          
hostname                                 gem-tstation
======================================== ============

Slowest sources
---------------
====== ========= ========================= ============ ========= ========= =========
grp_id source_id source_class              num_ruptures calc_time num_sites num_split
====== ========= ========================= ============ ========= ========= =========
4      CHAR1     CharacteristicFaultSource 1            0.0       1         0        
2      CHAR1     CharacteristicFaultSource 1            0.0       1         0        
9      CHAR1     CharacteristicFaultSource 1            0.0       1         0        
8      COMFLT1   ComplexFaultSource        29           0.0       1         0        
3      COMFLT1   ComplexFaultSource        62           0.0       1         0        
4      SFLT1     SimpleFaultSource         56           0.0       1         0        
1      SFLT1     SimpleFaultSource         56           0.0       1         0        
5      CHAR1     CharacteristicFaultSource 1            0.0       1         0        
10     CHAR1     CharacteristicFaultSource 1            0.0       1         0        
9      SFLT1     SimpleFaultSource         58           0.0       1         0        
7      SFLT1     SimpleFaultSource         58           0.0       1         0        
2      COMFLT1   ComplexFaultSource        29           0.0       1         0        
7      COMFLT1   ComplexFaultSource        29           0.0       1         0        
1      COMFLT1   ComplexFaultSource        29           0.0       1         0        
0      SFLT1     SimpleFaultSource         56           0.0       1         0        
8      SFLT1     SimpleFaultSource         58           0.0       1         0        
11     COMFLT1   ComplexFaultSource        62           0.0       1         0        
6      SFLT1     SimpleFaultSource         58           0.0       1         0        
3      SFLT1     SimpleFaultSource         56           0.0       1         0        
6      COMFLT1   ComplexFaultSource        29           0.0       1         0        
====== ========= ========================= ============ ========= ========= =========

Computation times by source typology
------------------------------------
========================= ========= ======
source_class              calc_time counts
========================= ========= ======
CharacteristicFaultSource 0.0       12    
ComplexFaultSource        0.0       12    
SimpleFaultSource         0.0       12    
========================= ========= ======

Information about the tasks
---------------------------
================== ========= ========= ========= ========= =========
operation-duration mean      stddev    min       max       num_tasks
count_eff_ruptures 8.633E-04 8.039E-05 7.489E-04 9.930E-04 12       
================== ========= ========= ========= ========= =========

Slowest operations
------------------
================================ ========= ========= ======
operation                        time_sec  memory_mb counts
================================ ========= ========= ======
reading composite source model   0.708     0.0       1     
filtering composite source model 0.041     0.0       1     
managing sources                 0.012     0.0       1     
total count_eff_ruptures         0.010     0.0       12    
store source_info                8.020E-04 0.0       1     
aggregate curves                 2.031E-04 0.0       12    
reading site collection          2.813E-05 0.0       1     
saving probability maps          2.599E-05 0.0       1     
================================ ========= ========= ======