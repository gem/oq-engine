Classical PSHA QA test
======================

============== ===================
checksum32     752,446,534        
date           2019-10-01T06:32:44
engine_version 3.8.0-git66affb82eb
============== ===================

num_sites = 21, num_levels = 26, num_rlzs = 4

Parameters
----------
=============================== ==================
calculation_mode                'preclassical'    
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              50.0              
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            4.0               
complex_fault_mesh_spacing      4.0               
width_of_mfd_bin                0.1               
area_source_discretization      10.0              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     23                
master_seed                     0                 
ses_seed                        42                
=============================== ==================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
sites                   `qa_sites.csv <qa_sites.csv>`_                              
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========================= ======= =============== ================
smlt_path                 weight  gsim_logic_tree num_realizations
========================= ======= =============== ================
aFault_aPriori_D2.1       0.50000 simple(2)       2               
bFault_stitched_D2.1_Char 0.50000 simple(2)       2               
========================= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ========================================= =========== ======================= =================
grp_id gsims                                     distances   siteparams              ruptparams       
====== ========================================= =========== ======================= =================
0      '[BooreAtkinson2008]' '[ChiouYoungs2008]' rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
1      '[BooreAtkinson2008]' '[ChiouYoungs2008]' rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
====== ========================================= =========== ======================= =================

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=8, rlzs=4)>

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      2,252     1,980        1,958       
1      2,170     2,706        2,310       
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============ =====
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures speed
========= ====== ==== ============ ========= ========= ============ =====
86_0      0      X    11           0.00334   15        11           3,290
76_1      0      X    11           0.00299   21        11           3,675
38_1      0      X    11           0.00292   14        11           3,773
4_1       0      X    11           0.00264   9.00000   11           4,161
19_1      0      X    11           0.00239   6.00000   11           4,599
0_0       0      X    11           0.00238   11        11           4,620
29_0      0      X    11           0.00237   15        11           4,639
57_1      0      X    11           0.00235   18        11           4,689
21_0      1      X    11           0.00216   4.00000   11           5,100
30_1      1      X    11           0.00213   8.00000   11           5,176
103_1     1      X    11           0.00205   14        11           5,354
48_0      0      X    11           0.00189   7.00000   11           5,805
69_1      1      X    11           0.00185   13        11           5,952
98_0      1      X    11           0.00182   15        11           6,037
79_0      1      X    11           0.00156   4.00000   11           7,049
88_1      1      X    11           0.00151   21        11           7,271
67_0      0      X    11           0.00144   21        11           7,644
113_0     1      X    11           0.00126   11        11           8,748
4_1       1      X    11           0.00123   15        11           8,945
122_1     1      X    11           0.00120   13        11           9,167
========= ====== ==== ============ ========= ========= ============ =====

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
X    0.11052   426   
==== ========= ======

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
SourceReader       1.26618 0.46381 0.93821 1.59414 2      
preclassical       0.00664 0.00200 0.00308 0.00959 21     
================== ======= ======= ======= ======= =======

Data transfer
-------------
============ =========================================== ========
task         sent                                        received
SourceReader apply_unc=8.36 KB ltmodel=434 B fname=228 B 1.84 MB 
preclassical srcs=1.48 MB params=15.89 KB gsims=5.58 KB  22.96 KB
============ =========================================== ========

Slowest operations
------------------
====================== ======== ========= ======
calc_6495              time_sec memory_mb counts
====================== ======== ========= ======
total SourceReader     2.53235  2.08203   2     
composite source model 1.63704  2.68359   1     
total preclassical     0.13952  0.25391   21    
aggregate curves       0.00589  0.0       21    
store source_info      0.00386  0.0       1     
====================== ======== ========= ======