Classical Hazard QA Test, Case 20
=================================

============== ===================
checksum32     1_447_978_906      
date           2020-03-13T11:22:54
engine_version 3.9.0-gitfb3ef3a732
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
pointsource_distance            {'default': {}}   
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
========================= ======= ================
smlt_path                 weight  num_realizations
========================= ======= ================
sm1_sg1_cog1_char_complex 0.07000 1               
sm1_sg1_cog1_char_plane   0.10500 1               
sm1_sg1_cog1_char_simple  0.17500 1               
sm1_sg1_cog2_char_complex 0.07000 1               
sm1_sg1_cog2_char_plane   0.10500 1               
sm1_sg1_cog2_char_simple  0.17500 1               
sm1_sg2_cog1_char_complex 0.03000 1               
sm1_sg2_cog1_char_plane   0.04500 1               
sm1_sg2_cog1_char_simple  0.07500 1               
sm1_sg2_cog2_char_complex 0.03000 1               
sm1_sg2_cog2_char_plane   0.04500 1               
sm1_sg2_cog2_char_simple  0.07500 1               
========================= ======= ================

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

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      0.04651   86           86          
1      1.00000   1            1.00000     
2      1.00000   1            1.00000     
3      0.01613   62           62          
6      0.03448   58           58          
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
SFLT1     0      S    56           0.00973   0.03571   56          
SFLT1     6      S    58           0.00944   0.03448   58          
COMFLT1   3      C    62           0.00581   0.01613   62          
COMFLT1   0      C    29           0.00522   0.03448   29          
CHAR1     0      X    1            0.00255   1.00000   1.00000     
CHAR1     1      X    1            3.805E-04 1.00000   1.00000     
CHAR1     2      X    1            2.062E-04 1.00000   1.00000     
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
C    0.01103  
S    0.01918  
X    0.00314  
==== =========

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
preclassical       0.00803 0.00277 0.00462 0.01111 5      
read_source_model  0.07634 NaN     0.07634 0.07634 1      
================== ======= ======= ======= ======= =======

Data transfer
-------------
================= ============================================== ========
task              sent                                           received
read_source_model                                                10.9 KB 
preclassical      srcs=25.07 KB params=3.15 KB srcfilter=1.09 KB 2 KB    
================= ============================================== ========

Slowest operations
------------------
=========================== ======== ========= ======
calc_66999                  time_sec memory_mb counts
=========================== ======== ========= ======
composite source model      0.98189  0.0       1     
total read_source_model     0.07634  0.0       1     
total preclassical          0.04015  0.48828   5     
splitting/filtering sources 0.00210  0.0       5     
store source_info           0.00205  0.0       1     
aggregate curves            0.00113  0.0       5     
=========================== ======== ========= ======