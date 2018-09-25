Classical Hazard QA Test, Case 20
=================================

============== ===================
checksum32     3,909,444,611      
date           2018-09-25T14:28:42
engine_version 3.3.0-git8ffb37de56
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
source                  `source_model.xml <source_model.xml>`_                      
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
#tot_weight   0    
============= =====

Slowest sources
---------------
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======
grp_id source_id code gidx1 gidx2 num_ruptures calc_time split_time num_sites num_split weight
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======
0      CHAR1     X    0     308   1            0.0       1.335E-05  0.0       1         0.0   
0      COMFLT1   C    308   312   29           0.0       1.621E-05  0.0       1         0.0   
0      SFLT1     S    312   314   56           0.0       2.108E-04  0.0       2         0.0   
1      CHAR1     X    0     8     1            0.0       5.722E-06  0.0       1         0.0   
1      COMFLT1   C    8     12    29           0.0       8.106E-06  0.0       1         0.0   
1      SFLT1     S    12    14    56           0.0       1.187E-04  0.0       2         0.0   
2      CHAR1     X    0     344   1            0.0       4.768E-06  0.0       1         0.0   
2      COMFLT1   C    344   348   29           0.0       7.153E-06  0.0       1         0.0   
2      SFLT1     S    348   350   56           0.0       1.054E-04  0.0       2         0.0   
3      CHAR1     X    0     308   1            0.0       4.292E-06  0.0       1         0.0   
3      COMFLT1   C    308   312   62           0.0       6.676E-06  0.0       1         0.0   
3      SFLT1     S    312   314   56           0.0       1.092E-04  0.0       2         0.0   
4      CHAR1     X    0     8     1            0.0       4.053E-06  0.0       1         0.0   
4      COMFLT1   C    8     12    62           0.0       6.676E-06  0.0       1         0.0   
4      SFLT1     S    12    14    56           0.0       1.006E-04  0.0       2         0.0   
5      CHAR1     X    0     344   1            0.0       4.053E-06  0.0       1         0.0   
5      COMFLT1   C    344   348   62           0.0       6.676E-06  0.0       1         0.0   
5      SFLT1     S    348   350   56           0.0       1.006E-04  0.0       2         0.0   
6      CHAR1     X    0     308   1            0.0       4.053E-06  0.0       1         0.0   
6      COMFLT1   C    308   312   29           0.0       6.199E-06  0.0       1         0.0   
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
================== ======= ====== ======= ======= =========
operation-duration mean    stddev min     max     num_tasks
read_source_models 0.07886 NaN    0.07886 0.07886 1        
split_filter       0.03809 NaN    0.03809 0.03809 1        
================== ======= ====== ======= ======= =========

Data transfer
-------------
================== ======================================================================== ========
task               sent                                                                     received
read_source_models monitor=0 B fnames=0 B converter=0 B                                     10.89 KB
split_filter       srcs=25.23 KB monitor=432 B srcfilter=253 B sample_factor=21 B seed=14 B 29.22 KB
================== ======================================================================== ========

Slowest operations
------------------
======================== ======== ========= ======
operation                time_sec memory_mb counts
======================== ======== ========= ======
total read_source_models 0.07886  0.0       1     
updating source_info     0.04955  0.0       1     
total split_filter       0.03809  0.0       1     
======================== ======== ========= ======