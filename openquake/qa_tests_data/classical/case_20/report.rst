Classical Hazard QA Test, Case 20
=================================

============== ===================
checksum32     1,888,120,170      
date           2019-10-02T10:07:35
engine_version 3.8.0-git6f03622c6e
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
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
SFLT1     6      S    58           0.00606   0.01724   58          
SFLT1     4      S    56           0.00564   0.01786   56          
SFLT1     5      S    56           0.00559   0.01786   56          
SFLT1     3      S    56           0.00558   0.01786   56          
COMFLT1   1      C    29           0.00496   0.03448   29          
COMFLT1   4      C    62           0.00483   0.01613   62          
SFLT1     11     S    58           0.00475   0.01724   58          
COMFLT1   3      C    62           0.00470   0.01613   62          
COMFLT1   11     C    62           0.00430   0.01613   62          
SFLT1     10     S    58           0.00421   0.01724   58          
COMFLT1   9      C    62           0.00419   0.01613   62          
SFLT1     8      S    58           0.00416   0.01724   58          
SFLT1     9      S    58           0.00411   0.01724   58          
COMFLT1   5      C    62           0.00403   0.01613   62          
SFLT1     1      S    56           0.00341   0.01786   56          
COMFLT1   10     C    62           0.00292   0.01613   62          
SFLT1     7      S    58           0.00263   0.01724   58          
COMFLT1   6      C    29           0.00249   0.03448   29          
COMFLT1   2      C    29           0.00244   0.03448   29          
COMFLT1   7      C    29           0.00243   0.03448   29          
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
C    0.04015   12    
S    0.04992   12    
X    0.00383   12    
==== ========= ======

Duplicated sources
------------------
Found 0 unique sources and 7 duplicate sources with multiplicity 5.1: ['CHAR1' 'CHAR1' 'CHAR1' 'COMFLT1' 'COMFLT1' 'SFLT1' 'SFLT1']

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
SourceReader       0.15289 0.01442 0.13390 0.17751 12     
preclassical       0.00572 0.00177 0.00326 0.00944 18     
================== ======= ======= ======= ======= =======

Data transfer
-------------
============ ================================================= =========
task         sent                                              received 
SourceReader apply_unc=249.08 KB ltmodel=2.53 KB fname=1.22 KB 141.46 KB
preclassical srcs=99.25 KB params=9.23 KB srcfilter=3.92 KB    6.85 KB  
============ ================================================= =========

Slowest operations
------------------
====================== ======== ========= ======
calc_29530             time_sec memory_mb counts
====================== ======== ========= ======
total SourceReader     1.83466  0.28125   12    
composite source model 0.37125  0.0       1     
total preclassical     0.10291  0.0       18    
aggregate curves       0.00528  0.0       18    
store source_info      0.00273  0.0       1     
====================== ======== ========= ======