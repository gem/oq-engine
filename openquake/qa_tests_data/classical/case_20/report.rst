Classical Hazard QA Test, Case 20
=================================

============== ===================
checksum32     1,888,120,170      
date           2019-05-03T06:44:09
engine_version 3.5.0-git7a6d15e809
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
#tot_weight   2,880
============= =====

Slowest sources
---------------
====== ========= ==== ===== ===== ============ ========= ========= =======
grp_id source_id code gidx1 gidx2 num_ruptures calc_time num_sites weight 
====== ========= ==== ===== ===== ============ ========= ========= =======
4      COMFLT1   C    1000  1,004 62           2.432E-05 1.00000   248    
1      COMFLT1   C    322   326   29           2.384E-05 1.00000   116    
9      SFLT1     S    2,346 2,348 58           2.289E-05 1.00000   58     
4      SFLT1     S    1,004 1,006 56           2.289E-05 1.00000   56     
0      CHAR1     X    0     308   1            2.289E-05 1.00000   1.00000
8      SFLT1     S    2,032 2,034 58           2.217E-05 1.00000   58     
3      COMFLT1   C    986   990   62           1.740E-05 1.00000   248    
10     CHAR1     X    2,348 2,356 1            1.574E-05 1.00000   1.00000
9      CHAR1     X    2,034 2,342 1            1.526E-05 1.00000   1.00000
2      COMFLT1   C    672   676   29           1.526E-05 1.00000   116    
2      CHAR1     X    328   672   1            1.502E-05 1.00000   1.00000
5      CHAR1     X    1,006 1,350 1            1.478E-05 1.00000   1.00000
5      SFLT1     S    1,354 1,356 56           1.407E-05 1.00000   56     
1      CHAR1     X    314   322   1            1.383E-05 1.00000   1.00000
6      SFLT1     S    1,668 1,670 58           1.359E-05 1.00000   58     
3      SFLT1     S    990   992   56           1.287E-05 1.00000   56     
11     COMFLT1   C    2,706 2,710 62           1.192E-05 1.00000   248    
9      COMFLT1   C    2,342 2,346 62           1.168E-05 1.00000   248    
10     SFLT1     S    2,360 2,362 58           1.073E-05 1.00000   58     
10     COMFLT1   C    2,356 2,360 62           1.049E-05 1.00000   248    
====== ========= ==== ===== ===== ============ ========= ========= =======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
C    1.490E-04 12    
S    1.624E-04 12    
X    1.473E-04 12    
==== ========= ======

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
read_source_models 0.07473 0.00497 0.06710 0.08358 12     
preclassical       0.00539 0.00226 0.00248 0.00958 18     
================== ======= ======= ======= ======= =======

Data transfer
-------------
================== ============================================================ =========
task               sent                                                         received 
read_source_models converter=3.67 KB fnames=1.25 KB                             131.54 KB
preclassical       srcs=98.88 KB params=8.54 KB srcfilter=3.83 KB gsims=2.58 KB 6.73 KB  
================== ============================================================ =========

Slowest operations
------------------
======================== ======== ========= ======
operation                time_sec memory_mb counts
======================== ======== ========= ======
total read_source_models 0.89676  0.0       12    
total preclassical       0.09695  0.0       18    
managing sources         0.00612  0.0       1     
aggregate curves         0.00289  0.0       18    
store source_info        0.00256  0.0       1     
======================== ======== ========= ======