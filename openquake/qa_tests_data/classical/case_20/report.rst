Classical Hazard QA Test, Case 20
=================================

============== ===================
checksum32     1,888,120,170      
date           2019-06-24T15:34:14
engine_version 3.6.0-git4b6205639c
============== ===================

num_sites = 1, num_levels = 4, num_rlzs = 12

Parameters
----------
=============================== ==================
calculation_mode                'preclassical'    
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
sm1_sg1_cog1_char_complex 0.07000 trivial(1)      1               
sm1_sg1_cog1_char_plane   0.10500 trivial(1)      1               
sm1_sg1_cog1_char_simple  0.17500 trivial(1)      1               
sm1_sg1_cog2_char_complex 0.07000 trivial(1)      1               
sm1_sg1_cog2_char_plane   0.10500 trivial(1)      1               
sm1_sg1_cog2_char_simple  0.17500 trivial(1)      1               
sm1_sg2_cog1_char_complex 0.03000 trivial(1)      1               
sm1_sg2_cog1_char_plane   0.04500 trivial(1)      1               
sm1_sg2_cog1_char_simple  0.07500 trivial(1)      1               
sm1_sg2_cog2_char_complex 0.03000 trivial(1)      1               
sm1_sg2_cog2_char_plane   0.04500 trivial(1)      1               
sm1_sg2_cog2_char_simple  0.07500 trivial(1)      1               
========================= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================== ========= ========== ==========
grp_id gsims              distances siteparams ruptparams
====== ================== ========= ========== ==========
0      '[SadighEtAl1997]' rrup      vs30       mag rake  
1      '[SadighEtAl1997]' rrup      vs30       mag rake  
2      '[SadighEtAl1997]' rrup      vs30       mag rake  
3      '[SadighEtAl1997]' rrup      vs30       mag rake  
4      '[SadighEtAl1997]' rrup      vs30       mag rake  
5      '[SadighEtAl1997]' rrup      vs30       mag rake  
6      '[SadighEtAl1997]' rrup      vs30       mag rake  
7      '[SadighEtAl1997]' rrup      vs30       mag rake  
8      '[SadighEtAl1997]' rrup      vs30       mag rake  
9      '[SadighEtAl1997]' rrup      vs30       mag rake  
10     '[SadighEtAl1997]' rrup      vs30       mag rake  
11     '[SadighEtAl1997]' rrup      vs30       mag rake  
====== ================== ========= ========== ==========

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=12, rlzs=12)>

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
#tot_weight   1,242
============= =====

Slowest sources
---------------
====== ========= ==== ===== ===== ============ ========= ========= ======= =============
grp_id source_id code gidx1 gidx2 num_ruptures calc_time num_sites weight  checksum     
====== ========= ==== ===== ===== ============ ========= ========= ======= =============
6      SFLT1     S    1,668 1,670 58           0.00587   1.00000   58      3,869,525,047
0      SFLT1     S    312   314   56           0.00581   1.00000   56      880,754,185  
3      COMFLT1   C    986   990   62           0.00277   1.00000   62      1,341,080,878
0      COMFLT1   C    308   312   29           0.00251   1.00000   29      2,140,554,186
2      CHAR1     X    328   672   1            0.00246   1.00000   1.00000 1,311,087,308
1      CHAR1     X    314   322   1            3.610E-04 1.00000   1.00000 2,334,678,879
0      CHAR1     X    0     308   1            2.043E-04 1.00000   1.00000 2,503,505,096
11     SFLT1     S    2,710 2,712 58           0.0       0.0       0.0     3,869,525,047
11     COMFLT1   C    2,706 2,710 62           0.0       0.0       0.0     1,341,080,878
11     CHAR1     X    2,362 2,706 1            0.0       0.0       0.0     1,311,087,308
10     SFLT1     S    2,360 2,362 58           0.0       0.0       0.0     3,869,525,047
10     COMFLT1   C    2,356 2,360 62           0.0       0.0       0.0     1,341,080,878
10     CHAR1     X    2,348 2,356 1            0.0       0.0       0.0     2,334,678,879
9      SFLT1     S    2,346 2,348 58           0.0       0.0       0.0     3,869,525,047
9      COMFLT1   C    2,342 2,346 62           0.0       0.0       0.0     1,341,080,878
9      CHAR1     X    2,034 2,342 1            0.0       0.0       0.0     2,503,505,096
8      SFLT1     S    2,032 2,034 58           0.0       0.0       0.0     3,869,525,047
8      COMFLT1   C    2,028 2,032 29           0.0       0.0       0.0     2,140,554,186
8      CHAR1     X    1,684 2,028 1            0.0       0.0       0.0     1,311,087,308
7      SFLT1     S    1,682 1,684 58           0.0       0.0       0.0     3,869,525,047
====== ========= ==== ===== ===== ============ ========= ========= ======= =============

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
C    0.00528   12    
S    0.01168   12    
X    0.00303   12    
==== ========= ======

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
preclassical       0.00726 0.00158 0.00632 0.00908 3      
read_source_models 0.08106 0.00713 0.06685 0.09059 12     
================== ======= ======= ======= ======= =======

Data transfer
-------------
================== ======================================================== =========
task               sent                                                     received 
preclassical       srcs=22.48 KB params=1.42 KB srcfilter=660 B gsims=441 B 1.26 KB  
read_source_models converter=3.67 KB fnames=1.25 KB                         131.65 KB
================== ======================================================== =========

Slowest operations
------------------
======================== ========= ========= ======
operation                time_sec  memory_mb counts
======================== ========= ========= ======
total read_source_models 0.97267   0.0       12    
total preclassical       0.02178   0.0       3     
managing sources         0.00322   0.0       1     
store source_info        0.00155   0.0       1     
aggregate curves         6.158E-04 0.0       3     
======================== ========= ========= ======