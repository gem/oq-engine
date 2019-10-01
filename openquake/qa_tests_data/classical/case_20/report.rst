Classical Hazard QA Test, Case 20
=================================

============== ===================
checksum32     1,888,120,170      
date           2019-10-01T06:32:42
engine_version 3.8.0-git66affb82eb
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

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      3.00000   86           86          
1      3.00000   86           86          
2      3.00000   86           86          
3      3.00000   119          119         
4      3.00000   119          119         
5      3.00000   119          119         
6      3.00000   88           88          
7      3.00000   88           88          
8      3.00000   88           88          
9      3.00000   121          121         
10     3.00000   121          121         
11     3.00000   121          121         
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============ ======
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures speed 
========= ====== ==== ============ ========= ========= ============ ======
SFLT1     6      S    58           0.00627   1.00000   58           9,251 
SFLT1     3      S    56           0.00536   1.00000   56           10,440
SFLT1     9      S    58           0.00533   1.00000   58           10,881
SFLT1     7      S    58           0.00517   1.00000   58           11,222
COMFLT1   2      C    29           0.00511   1.00000   29           5,677 
COMFLT1   4      C    62           0.00498   1.00000   62           12,459
SFLT1     8      S    58           0.00463   1.00000   58           12,535
COMFLT1   3      C    62           0.00424   1.00000   62           14,628
SFLT1     5      S    56           0.00419   1.00000   56           13,380
COMFLT1   10     C    62           0.00404   1.00000   62           15,349
COMFLT1   11     C    62           0.00387   1.00000   62           16,032
SFLT1     10     S    58           0.00369   1.00000   58           15,720
SFLT1     2      S    56           0.00352   1.00000   56           15,888
SFLT1     0      S    56           0.00351   1.00000   56           15,935
COMFLT1   5      C    62           0.00315   1.00000   62           19,681
COMFLT1   9      C    62           0.00314   1.00000   62           19,765
CHAR1     0      X    1            0.00306   1.00000   1.00000      327   
SFLT1     4      S    56           0.00298   1.00000   56           18,793
SFLT1     11     S    58           0.00275   1.00000   58           21,055
COMFLT1   0      C    29           0.00265   1.00000   29           10,931
========= ====== ==== ============ ========= ========= ============ ======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
C    0.04038   12    
S    0.04945   12    
X    0.00548   12    
==== ========= ======

Duplicated sources
------------------
Found 0 unique sources and 7 duplicate sources with multiplicity 5.1: ['CHAR1' 'CHAR1' 'CHAR1' 'COMFLT1' 'COMFLT1' 'SFLT1' 'SFLT1']

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
SourceReader       0.14663 0.01460 0.12656 0.17699 12     
preclassical       0.00578 0.00227 0.00303 0.01019 18     
================== ======= ======= ======= ======= =======

Data transfer
-------------
============ ================================================= =========
task         sent                                              received 
SourceReader apply_unc=249.08 KB ltmodel=2.53 KB fname=1.22 KB 132.02 KB
preclassical srcs=99.25 KB params=9.23 KB srcfilter=3.9 KB     6.85 KB  
============ ================================================= =========

Slowest operations
------------------
====================== ======== ========= ======
calc_6488              time_sec memory_mb counts
====================== ======== ========= ======
total SourceReader     1.75957  0.21094   12    
composite source model 0.35892  0.0       1     
total preclassical     0.10409  0.0       18    
aggregate curves       0.00521  0.0       18    
store source_info      0.00259  0.0       1     
====================== ======== ========= ======