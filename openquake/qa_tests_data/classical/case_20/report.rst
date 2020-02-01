Classical Hazard QA Test, Case 20
=================================

============== ===================
checksum32     1_447_978_906      
date           2020-01-16T05:31:49
engine_version 3.8.0-git83c45f7244
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
pointsource_distance            None              
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
0      0.04651   86           86          
1      1.00000   86           1.00000     
2      1.00000   86           1.00000     
3      0.01613   119          62          
4      NaN       119          0.0         
5      NaN       119          0.0         
6      0.03448   88           58          
7      NaN       88           0.0         
8      NaN       88           0.0         
9      NaN       121          0.0         
10     NaN       121          0.0         
11     NaN       121          0.0         
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
SFLT1     6      S    58           0.00915   0.03448   58          
SFLT1     0      S    56           0.00802   0.03571   56          
COMFLT1   0      C    29           0.00448   0.03448   29          
COMFLT1   3      C    62           0.00325   0.01613   62          
CHAR1     0      X    1            0.00242   1.00000   1.00000     
CHAR1     1      X    1            2.978E-04 1.00000   1.00000     
CHAR1     2      X    1            2.060E-04 1.00000   1.00000     
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
C    0.00773  
S    0.01716  
X    0.00292  
==== =========

Duplicated sources
------------------
Found 0 unique sources and 7 duplicate sources with multiplicity 5.1: ['CHAR1' 'CHAR1' 'CHAR1' 'COMFLT1' 'COMFLT1' 'SFLT1' 'SFLT1']

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
SourceReader       0.15539 0.01893 0.13450 0.19696 12     
preclassical       0.00673 0.00294 0.00412 0.01048 5      
================== ======= ======= ======= ======= =======

Data transfer
-------------
============ ================================================= =========
task         sent                                              received 
SourceReader apply_unc=249.08 KB ltmodel=2.53 KB fname=1.22 KB 120.82 KB
preclassical srcs=23.76 KB params=3.28 KB srcfilter=1.09 KB    2 KB     
============ ================================================= =========

Slowest operations
------------------
=========================== ======== ========= ======
calc_43328                  time_sec memory_mb counts
=========================== ======== ========= ======
total SourceReader          1.86472  0.0       12    
composite source model      0.38953  0.0       1     
total preclassical          0.03366  0.29297   5     
store source_info           0.00215  0.0       1     
splitting/filtering sources 0.00170  0.0       5     
aggregate curves            0.00102  0.0       5     
=========================== ======== ========= ======