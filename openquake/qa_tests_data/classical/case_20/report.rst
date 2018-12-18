Classical Hazard QA Test, Case 20
=================================

============== ===================
checksum32     3,909,444,611      
date           2018-12-13T12:58:00
engine_version 3.3.0-git68d7d11268
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
0      CHAR1     X    0     308   1            0.0       1.597E-05  0.0       1         0.0   
0      COMFLT1   C    308   312   29           0.0       1.454E-05  0.0       1         0.0   
0      SFLT1     S    312   314   56           0.0       1.554E-04  0.0       2         0.0   
1      CHAR1     X    0     8     1            0.0       5.245E-06  0.0       1         0.0   
1      COMFLT1   C    8     12    29           0.0       6.437E-06  0.0       1         0.0   
1      SFLT1     S    12    14    56           0.0       8.011E-05  0.0       2         0.0   
2      CHAR1     X    0     344   1            0.0       4.292E-06  0.0       1         0.0   
2      COMFLT1   C    344   348   29           0.0       5.484E-06  0.0       1         0.0   
2      SFLT1     S    348   350   56           0.0       6.962E-05  0.0       2         0.0   
3      CHAR1     X    0     308   1            0.0       4.053E-06  0.0       1         0.0   
3      COMFLT1   C    308   312   62           0.0       5.484E-06  0.0       1         0.0   
3      SFLT1     S    312   314   56           0.0       6.819E-05  0.0       2         0.0   
4      CHAR1     X    0     8     1            0.0       3.576E-06  0.0       1         0.0   
4      COMFLT1   C    8     12    62           0.0       5.245E-06  0.0       1         0.0   
4      SFLT1     S    12    14    56           0.0       6.628E-05  0.0       2         0.0   
5      CHAR1     X    0     344   1            0.0       3.576E-06  0.0       1         0.0   
5      COMFLT1   C    344   348   62           0.0       5.007E-06  0.0       1         0.0   
5      SFLT1     S    348   350   56           0.0       7.725E-05  0.0       2         0.0   
6      CHAR1     X    0     308   1            0.0       3.576E-06  0.0       1         0.0   
6      COMFLT1   C    308   312   29           0.0       4.768E-06  0.0       1         0.0   
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
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
read_source_models 0.12383 0.03234 0.07153 0.15100 12     
split_filter       0.06173 NaN     0.06173 0.06173 1      
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
total read_source_models 1.48594  0.11719   12    
total split_filter       0.06173  0.0       1     
======================== ======== ========= ======