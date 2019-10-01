Classical Hazard QA Test, Case 20
=================================

============== ===================
checksum32     1,888,120,170      
date           2019-10-01T07:01:13
engine_version 3.8.0-gitbd71c2f960
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
COMFLT1   3      C    62           0.00593   1.00000   62           10,461
SFLT1     8      S    58           0.00578   1.00000   58           10,033
SFLT1     3      S    56           0.00572   1.00000   56           9,789 
SFLT1     4      S    56           0.00567   1.00000   56           9,868 
SFLT1     9      S    58           0.00547   1.00000   58           10,610
COMFLT1   5      C    62           0.00475   1.00000   62           13,052
COMFLT1   9      C    62           0.00458   1.00000   62           13,544
SFLT1     5      S    56           0.00439   1.00000   56           12,765
COMFLT1   10     C    62           0.00411   1.00000   62           15,075
SFLT1     7      S    58           0.00359   1.00000   58           16,144
COMFLT1   11     C    62           0.00314   1.00000   62           19,729
COMFLT1   2      C    29           0.00309   1.00000   29           9,376 
SFLT1     0      S    56           0.00308   1.00000   56           18,171
COMFLT1   0      C    29           0.00293   1.00000   29           9,908 
SFLT1     6      S    58           0.00266   1.00000   58           21,824
SFLT1     10     S    58           0.00259   1.00000   58           22,394
COMFLT1   1      C    29           0.00258   1.00000   29           11,238
SFLT1     11     S    58           0.00239   1.00000   58           24,225
COMFLT1   4      C    62           0.00239   1.00000   62           25,976
CHAR1     0      X    1            0.00224   1.00000   1.00000      445   
========= ====== ==== ============ ========= ========= ============ ======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
C    0.03784   12    
S    0.04514   12    
X    0.00441   12    
==== ========= ======

Duplicated sources
------------------
Found 0 unique sources and 7 duplicate sources with multiplicity 5.1: ['CHAR1' 'CHAR1' 'CHAR1' 'COMFLT1' 'COMFLT1' 'SFLT1' 'SFLT1']

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
SourceReader       0.15222 0.01638 0.13225 0.19499 12     
preclassical       0.00535 0.00168 0.00263 0.00919 18     
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
calc_6643              time_sec memory_mb counts
====================== ======== ========= ======
total SourceReader     1.82664  0.25391   12    
composite source model 0.39808  0.0       1     
total preclassical     0.09622  0.0       18    
aggregate curves       0.00475  0.0       18    
store source_info      0.00208  0.0       1     
====================== ======== ========= ======