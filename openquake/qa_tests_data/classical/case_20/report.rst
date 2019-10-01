Classical Hazard QA Test, Case 20
=================================

============== ===================
checksum32     1,888,120,170      
date           2019-10-01T06:08:57
engine_version 3.8.0-gite0871b5c35
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
3      3.00000   86           86          
6      3.00000   86           86          
9      3.00000   119          119         
12     3.00000   119          119         
15     3.00000   119          119         
18     3.00000   88           88          
21     3.00000   88           88          
24     3.00000   88           88          
27     3.00000   121          121         
30     3.00000   121          121         
33     3.00000   121          121         
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============ ======
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures speed 
========= ====== ==== ============ ========= ========= ============ ======
COMFLT1   5      C    62           0.00630   1.00000   62           9,837 
COMFLT1   8      C    29           0.00525   1.00000   29           5,527 
SFLT1     2      S    56           0.00430   1.00000   56           13,011
SFLT1     1      S    56           0.00387   1.00000   56           14,464
SFLT1     6      S    58           0.00374   1.00000   58           15,512
SFLT1     9      S    58           0.00366   1.00000   58           15,838
SFLT1     10     S    58           0.00354   1.00000   58           16,405
COMFLT1   4      C    62           0.00333   1.00000   62           18,637
COMFLT1   3      C    62           0.00322   1.00000   62           19,250
COMFLT1   1      C    29           0.00296   1.00000   29           9,797 
SFLT1     0      S    56           0.00268   1.00000   56           20,914
SFLT1     8      S    58           0.00237   1.00000   58           24,503
SFLT1     4      S    56           0.00233   1.00000   56           24,016
SFLT1     11     S    58           0.00232   1.00000   58           25,012
COMFLT1   10     C    62           0.00228   1.00000   62           27,210
SFLT1     5      S    56           0.00226   1.00000   56           24,800
SFLT1     3      S    56           0.00224   1.00000   56           24,963
SFLT1     7      S    58           0.00219   1.00000   58           26,425
COMFLT1   0      C    29           0.00184   1.00000   29           15,782
COMFLT1   9      C    62           0.00178   1.00000   62           34,929
========= ====== ==== ============ ========= ========= ============ ======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
C    0.03364   12    
S    0.03550   12    
X    0.00350   12    
==== ========= ======

Duplicated sources
------------------
Found 0 unique sources and 7 duplicate sources with multiplicity 5.1: ['CHAR1' 'CHAR1' 'CHAR1' 'COMFLT1' 'COMFLT1' 'SFLT1' 'SFLT1']

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
SourceReader       0.29511 0.02714 0.26041 0.34860 12     
preclassical       0.00792 0.00286 0.00269 0.01138 10     
================== ======= ======= ======= ======= =======

Data transfer
-------------
============ ================================================= =========
task         sent                                              received 
SourceReader apply_unc=248.84 KB ltmodel=2.53 KB fname=1.14 KB 131.94 KB
preclassical srcs=93.67 KB params=5.13 KB srcfilter=2.18 KB    4.52 KB  
============ ================================================= =========

Slowest operations
------------------
====================== ======== ========= ======
calc_23189             time_sec memory_mb counts
====================== ======== ========= ======
total SourceReader     3.54129  0.0       12    
composite source model 1.04502  0.0       1     
total preclassical     0.07917  0.0       10    
aggregate curves       0.00344  0.0       10    
store source_info      0.00223  0.0       1     
====================== ======== ========= ======