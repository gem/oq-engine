Classical Hazard QA Test, Case 20
=================================

============== ===================
checksum32     1,447,978,906      
date           2019-10-23T16:26:42
engine_version 3.8.0-git2e0d8e6795
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
0      0.03488   86           86          
1      0.03488   86           86          
2      0.03488   86           86          
3      0.02521   119          119         
4      0.02521   119          119         
5      0.02521   119          119         
6      0.03409   88           88          
7      0.03409   88           88          
8      0.03409   88           88          
9      0.02479   121          121         
10     0.02479   121          121         
11     0.02479   121          121         
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
COMFLT1   3      C    62           0.00647   0.01613   62          
SFLT1     4      S    56           0.00280   0.01786   56          
SFLT1     9      S    58           0.00278   0.01724   58          
SFLT1     3      S    56           0.00276   0.01786   56          
SFLT1     6      S    58           0.00274   0.01724   58          
SFLT1     0      S    56           0.00274   0.01786   56          
SFLT1     2      S    56           0.00273   0.01786   56          
SFLT1     10     S    58           0.00272   0.01724   58          
SFLT1     1      S    56           0.00270   0.01786   56          
SFLT1     11     S    58           0.00261   0.01724   58          
SFLT1     5      S    56           0.00249   0.01786   56          
SFLT1     8      S    58           0.00245   0.01724   58          
SFLT1     7      S    58           0.00245   0.01724   58          
COMFLT1   10     C    62           0.00243   0.01613   62          
COMFLT1   8      C    29           0.00236   0.03448   29          
COMFLT1   2      C    29           0.00235   0.03448   29          
COMFLT1   9      C    62           0.00234   0.01613   62          
COMFLT1   4      C    62           0.00234   0.01613   62          
COMFLT1   6      C    29           0.00230   0.03448   29          
COMFLT1   11     C    62           0.00224   0.01613   62          
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
C    0.03028  
S    0.03197  
X    0.00261  
==== =========

Duplicated sources
------------------
Found 0 unique sources and 7 duplicate sources with multiplicity 5.1: ['CHAR1' 'CHAR1' 'CHAR1' 'COMFLT1' 'COMFLT1' 'SFLT1' 'SFLT1']

Information about the tasks
---------------------------
================== ======= ========= ======= ======= =======
operation-duration mean    stddev    min     max     outputs
SourceReader       0.29685 0.05152   0.14784 0.34612 12     
preclassical       0.00299 8.591E-04 0.00224 0.00675 24     
================== ======= ========= ======= ======= =======

Data transfer
-------------
============ ================================================= =========
task         sent                                              received 
SourceReader apply_unc=249.08 KB ltmodel=2.53 KB fname=1.22 KB 140.94 KB
preclassical srcs=102.93 KB params=13.29 KB srcfilter=5.23 KB  8.6 KB   
============ ================================================= =========

Slowest operations
------------------
====================== ======== ========= ======
calc_44544             time_sec memory_mb counts
====================== ======== ========= ======
total SourceReader     3.56221  0.24219   12    
composite source model 0.73996  0.0       1     
total preclassical     0.07165  0.0       24    
aggregate curves       0.00912  0.0       24    
store source_info      0.00250  0.0       1     
====================== ======== ========= ======