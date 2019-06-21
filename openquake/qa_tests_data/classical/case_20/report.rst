Classical Hazard QA Test, Case 20
=================================

============== ===================
checksum32     1,888,120,170      
date           2019-06-21T09:42:39
engine_version 3.6.0-git17fd0581aa
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

  <RlzsAssoc(size=12, rlzs=12)
  0,'[SadighEtAl1997]': [0]
  1,'[SadighEtAl1997]': [1]
  2,'[SadighEtAl1997]': [2]
  3,'[SadighEtAl1997]': [3]
  4,'[SadighEtAl1997]': [4]
  5,'[SadighEtAl1997]': [5]
  6,'[SadighEtAl1997]': [6]
  7,'[SadighEtAl1997]': [7]
  8,'[SadighEtAl1997]': [8]
  9,'[SadighEtAl1997]': [9]
  10,'[SadighEtAl1997]': [10]
  11,'[SadighEtAl1997]': [11]>

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
====== ========= ==== ===== ===== ============ ========= ========= =======
grp_id source_id code gidx1 gidx2 num_ruptures calc_time num_sites weight 
====== ========= ==== ===== ===== ============ ========= ========= =======
4      SFLT1     S    1,004 1,006 56           0.01447   1.00000   56     
6      SFLT1     S    1,668 1,670 58           0.00623   1.00000   58     
5      SFLT1     S    1,354 1,356 56           0.00595   1.00000   56     
7      SFLT1     S    1,682 1,684 58           0.00532   1.00000   58     
10     SFLT1     S    2,360 2,362 58           0.00528   1.00000   58     
8      SFLT1     S    2,032 2,034 58           0.00499   1.00000   58     
3      COMFLT1   C    986   990   62           0.00497   1.00000   62     
1      COMFLT1   C    322   326   29           0.00496   1.00000   29     
4      COMFLT1   C    1000  1,004 62           0.00496   1.00000   62     
3      SFLT1     S    990   992   56           0.00466   1.00000   56     
9      COMFLT1   C    2,342 2,346 62           0.00455   1.00000   62     
0      SFLT1     S    312   314   56           0.00348   1.00000   56     
1      SFLT1     S    326   328   56           0.00341   1.00000   56     
7      COMFLT1   C    1,678 1,682 29           0.00278   1.00000   29     
0      COMFLT1   C    308   312   29           0.00275   1.00000   29     
0      CHAR1     X    0     308   1            0.00273   1.00000   1.00000
11     SFLT1     S    2,710 2,712 58           0.00270   1.00000   58     
9      SFLT1     S    2,346 2,348 58           0.00264   1.00000   58     
2      COMFLT1   C    672   676   29           0.00253   1.00000   29     
10     COMFLT1   C    2,356 2,360 62           0.00233   1.00000   62     
====== ========= ==== ===== ===== ============ ========= ========= =======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
C    0.03682   12    
S    0.06069   12    
X    0.00495   12    
==== ========= ======

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
preclassical       0.00612 0.00333 0.00235 0.01504 18     
read_source_models 0.08333 0.00812 0.06717 0.09460 12     
================== ======= ======= ======= ======= =======

Data transfer
-------------
================== ============================================================ =========
task               sent                                                         received 
preclassical       srcs=98.88 KB params=8.54 KB srcfilter=3.87 KB gsims=2.58 KB 6.88 KB  
read_source_models converter=3.67 KB fnames=1.25 KB                             131.54 KB
================== ============================================================ =========

Slowest operations
------------------
======================== ======== ========= ======
operation                time_sec memory_mb counts
======================== ======== ========= ======
total read_source_models 1.00001  0.0       12    
total preclassical       0.11014  0.0       18    
managing sources         0.00626  0.0       1     
aggregate curves         0.00358  0.0       18    
store source_info        0.00225  0.0       1     
======================== ======== ========= ======