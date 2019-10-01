Classical PSHA QA test
======================

============== ===================
checksum32     752,446,534        
date           2019-10-01T06:08:40
engine_version 3.8.0-gite0871b5c35
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
246    2,170     2,706        2,310       
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============ ======
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures speed 
========= ====== ==== ============ ========= ========= ============ ======
118_1     1      X    11           0.01826   11        11           602   
75_1      1      X    11           0.00720   10        11           1,527 
21_0      1      X    11           0.00695   4.00000   11           1,582 
92_1      1      X    11           0.00561   8.00000   11           1,961 
1_1       1      X    11           0.00496   13        11           2,220 
27_1      1      X    11           0.00480   7.00000   11           2,291 
76_0      0      X    11           0.00461   21        11           2,384 
98_0      1      X    11           0.00330   15        11           3,332 
81_1      0      X    11           0.00312   9.00000   11           3,530 
33_1      0      X    11           0.00203   21        11           5,426 
114_0     1      X    11           0.00190   12        11           5,787 
51_0      1      X    11           0.00180   8.00000   11           6,104 
0_0       0      X    11           0.00179   11        11           6,139 
58_0      0      X    11           0.00162   16        11           6,787 
81_0      1      X    11           6.690E-04 5.00000   11           16,442
66_0      1      X    11           6.602E-04 12        11           16,662
81_1      1      X    11           6.220E-04 5.00000   11           17,684
57_1      0      X    11           6.113E-04 18        11           17,994
4_0       1      X    11           5.910E-04 15        11           18,611
55_1      0      X    11           5.617E-04 7.00000   11           19,583
========= ====== ==== ============ ========= ========= ============ ======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
X    0.12966   426   
==== ========= ======

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
SourceReader       1.46447 0.49374 1.11534 1.81360 2      
preclassical       0.01865 0.01181 0.00233 0.03979 9      
================== ======= ======= ======= ======= =======

Data transfer
-------------
============ ========================================== ========
task         sent                                       received
SourceReader apply_unc=8.3 KB ltmodel=434 B fname=214 B 1.84 MB 
preclassical srcs=1.47 MB params=6.82 KB gsims=2.39 KB  19.44 KB
============ ========================================== ========

Slowest operations
------------------
====================== ======== ========= ======
calc_23165             time_sec memory_mb counts
====================== ======== ========= ======
total SourceReader     2.92893  2.55469   2     
composite source model 1.85658  1.54297   1     
total preclassical     0.16781  0.25781   9     
aggregate curves       0.00590  0.0       9     
store source_info      0.00551  0.0       1     
====================== ======== ========= ======