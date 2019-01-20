Classical Hazard QA Test, Case 20
=================================

============== ===================
checksum32     1,888,120,170      
date           2019-01-20T07:39:50
engine_version 3.4.0-git452d0c6835
============== ===================

num_sites = 1, num_levels = 4

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
minimum_intensity               {}                
random_seed                     106               
master_seed                     0                 
ses_seed                        42                
=============================== ==================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gsim_logic_tree.xml <gsim_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========================= ======= =============== ================
smlt_path                 weight  gsim_logic_tree num_realizations
========================= ======= =============== ================
sm1_sg1_cog1_char_complex 0.07000 trivial(1)      1/1             
sm1_sg1_cog1_char_plane   0.10500 trivial(1)      1/1             
sm1_sg1_cog1_char_simple  0.17500 trivial(1)      1/1             
sm1_sg1_cog2_char_complex 0.07000 trivial(1)      1/1             
sm1_sg1_cog2_char_plane   0.10500 trivial(1)      1/1             
sm1_sg1_cog2_char_simple  0.17500 trivial(1)      1/1             
sm1_sg2_cog1_char_complex 0.03000 trivial(1)      1/1             
sm1_sg2_cog1_char_plane   0.04500 trivial(1)      1/1             
sm1_sg2_cog1_char_simple  0.07500 trivial(1)      1/1             
sm1_sg2_cog2_char_complex 0.03000 trivial(1)      1/1             
sm1_sg2_cog2_char_plane   0.04500 trivial(1)      1/1             
sm1_sg2_cog2_char_simple  0.07500 trivial(1)      1/1             
========================= ======= =============== ================

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
====== ================ ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=12, rlzs=12)
  0,SadighEtAl1997(): [0]
  1,SadighEtAl1997(): [1]
  2,SadighEtAl1997(): [2]
  3,SadighEtAl1997(): [3]
  4,SadighEtAl1997(): [4]
  5,SadighEtAl1997(): [5]
  6,SadighEtAl1997(): [6]
  7,SadighEtAl1997(): [7]
  8,SadighEtAl1997(): [8]
  9,SadighEtAl1997(): [9]
  10,SadighEtAl1997(): [10]
  11,SadighEtAl1997(): [11]>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== ============ ============
source_model     grp_id trt                  eff_ruptures tot_ruptures
================ ====== ==================== ============ ============
source_model.xml 0      Active Shallow Crust 86           86          
source_model.xml 1      Active Shallow Crust 86           86          
source_model.xml 2      Active Shallow Crust 86           86          
source_model.xml 3      Active Shallow Crust 119          86          
source_model.xml 4      Active Shallow Crust 119          86          
source_model.xml 5      Active Shallow Crust 119          86          
source_model.xml 6      Active Shallow Crust 88           86          
source_model.xml 7      Active Shallow Crust 88           86          
source_model.xml 8      Active Shallow Crust 88           86          
source_model.xml 9      Active Shallow Crust 121          86          
source_model.xml 10     Active Shallow Crust 121          86          
source_model.xml 11     Active Shallow Crust 121          86          
================ ====== ==================== ============ ============

============= =====
#TRT models   12   
#eff_ruptures 1,242
#tot_ruptures 1,032
#tot_weight   2,880
============= =====

Slowest sources
---------------
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======
grp_id source_id code gidx1 gidx2 num_ruptures calc_time split_time num_sites num_split weight
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======
0      CHAR1     X    0     308   1            0.0       9.298E-06  0.0       1         0.0   
0      COMFLT1   C    308   312   29           0.0       7.391E-06  0.0       1         0.0   
0      SFLT1     S    312   314   56           0.0       1.082E-04  0.0       2         0.0   
1      CHAR1     X    314   322   1            0.0       3.576E-06  0.0       1         0.0   
1      COMFLT1   C    322   326   29           0.0       4.053E-06  0.0       1         0.0   
1      SFLT1     S    326   328   56           0.0       5.102E-05  0.0       2         0.0   
2      CHAR1     X    328   672   1            0.0       2.384E-06  0.0       1         0.0   
2      COMFLT1   C    672   676   29           0.0       3.099E-06  0.0       1         0.0   
2      SFLT1     S    676   678   56           0.0       4.196E-05  0.0       2         0.0   
3      CHAR1     X    678   986   1            0.0       2.146E-06  0.0       1         0.0   
3      COMFLT1   C    986   990   62           0.0       2.861E-06  0.0       1         0.0   
3      SFLT1     S    990   992   56           0.0       3.910E-05  0.0       2         0.0   
4      CHAR1     X    992   1000  1            0.0       2.146E-06  0.0       1         0.0   
4      COMFLT1   C    1000  1,004 62           0.0       2.861E-06  0.0       1         0.0   
4      SFLT1     S    1,004 1,006 56           0.0       3.719E-05  0.0       2         0.0   
5      CHAR1     X    1,006 1,350 1            0.0       2.146E-06  0.0       1         0.0   
5      COMFLT1   C    1,350 1,354 62           0.0       2.861E-06  0.0       1         0.0   
5      SFLT1     S    1,354 1,356 56           0.0       3.767E-05  0.0       2         0.0   
6      CHAR1     X    1,356 1,664 1            0.0       2.384E-06  0.0       1         0.0   
6      COMFLT1   C    1,664 1,668 29           0.0       2.861E-06  0.0       1         0.0   
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
C    0.0       12    
S    0.0       12    
X    0.0       12    
==== ========= ======

Duplicated sources
------------------
Found 3 source(s) with the same ID and 0 true duplicate(s)
Here is a fake duplicate: COMFLT1

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
read_source_models 0.06887 0.01736 0.06043 0.12199 12     
split_filter       0.04843 NaN     0.04843 0.04843 1      
================== ======= ======= ======= ======= =======

Data transfer
-------------
================== ======================================= =========
task               sent                                    received 
read_source_models converter=4.55 KB fnames=1.25 KB        130.63 KB
split_filter       srcs=25.37 KB srcfilter=253 B seed=14 B 29.41 KB 
================== ======================================= =========

Slowest operations
------------------
======================== ======== ========= ======
operation                time_sec memory_mb counts
======================== ======== ========= ======
total read_source_models 0.82642  1.17188   12    
total split_filter       0.04843  1.61719   1     
======================== ======== ========= ======