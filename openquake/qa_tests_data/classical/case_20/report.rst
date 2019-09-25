Classical Hazard QA Test, Case 20
=================================

============== ===================
checksum32     1,888,120,170      
date           2019-09-24T15:21:21
engine_version 3.7.0-git749bb363b3
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
source_model.xml 0      Active Shallow Crust 150          86          
source_model.xml 1      Active Shallow Crust 150          86          
source_model.xml 2      Active Shallow Crust 150          86          
source_model.xml 3      Active Shallow Crust 150          86          
source_model.xml 4      Active Shallow Crust 150          86          
source_model.xml 5      Active Shallow Crust 150          86          
source_model.xml 6      Active Shallow Crust 152          86          
source_model.xml 7      Active Shallow Crust 152          86          
source_model.xml 8      Active Shallow Crust 152          86          
source_model.xml 9      Active Shallow Crust 152          86          
source_model.xml 10     Active Shallow Crust 152          86          
source_model.xml 11     Active Shallow Crust 152          86          
================ ====== ==================== ============ ============

============= =====
#TRT models   12   
#eff_ruptures 1,812
#tot_ruptures 1,032
============= =====

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============ ======
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures speed 
========= ====== ==== ============ ========= ========= ============ ======
SFLT1     0      S    56           0.00704   2.00000   114          16,198
COMFLT1   0      C    29           0.00516   2.00000   91           17,629
CHAR1     0      X    1            7.570E-04 3.00000   3.00000      3,963 
========= ====== ==== ============ ========= ========= ============ ======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
C    0.00516   12    
S    0.00704   12    
X    7.570E-04 12    
==== ========= ======

Duplicated sources
------------------
Found 0 unique sources and 7 duplicate sources with multiplicity 5.1: ['CHAR1' 'CHAR1' 'CHAR1' 'COMFLT1' 'COMFLT1' 'SFLT1' 'SFLT1']

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
preclassical       0.00490 0.00149 0.00392 0.00661 3      
read_source_models 0.08053 0.00687 0.06535 0.08851 12     
================== ======= ======= ======= ======= =======

Data transfer
-------------
================== ============================================ =========
task               sent                                         received 
preclassical       srcs=22.5 KB srcfilter=1.9 KB params=1.54 KB 1.13 KB  
read_source_models converter=3.68 KB fnames=1.25 KB             131.65 KB
================== ============================================ =========

Slowest operations
------------------
======================== ========= ========= ======
calc_1835                time_sec  memory_mb counts
======================== ========= ========= ======
total read_source_models 0.96640   0.00781   12    
total preclassical       0.01469   0.0       3     
store source_info        0.00204   0.0       1     
aggregate curves         0.00126   0.0       3     
managing sources         3.819E-04 0.0       1     
======================== ========= ========= ======