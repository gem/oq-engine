Classical PSHA QA test
======================

============== ===================
checksum32     752,446,534        
date           2019-10-01T07:01:15
engine_version 3.8.0-gitbd71c2f960
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
========= ====== ==== ============ ========= ========= ============ ======
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures speed 
========= ====== ==== ============ ========= ========= ============ ======
38_1      0      X    11           0.00282   14        11           3,906 
76_1      0      X    11           0.00275   21        11           4,004 
67_0      0      X    11           0.00261   21        11           4,217 
19_1      0      X    11           0.00250   6.00000   11           4,394 
29_0      0      X    11           0.00237   15        11           4,641 
30_1      1      X    11           0.00234   8.00000   11           4,694 
0_0       0      X    11           0.00231   11        11           4,765 
48_0      0      X    11           0.00229   7.00000   11           4,799 
122_1     1      X    11           0.00219   13        11           5,029 
21_0      1      X    11           0.00215   4.00000   11           5,115 
4_1       1      X    11           0.00195   15        11           5,653 
88_1      1      X    11           0.00188   21        11           5,846 
98_0      1      X    11           0.00188   15        11           5,862 
79_0      1      X    11           0.00166   4.00000   11           6,633 
86_0      0      X    11           0.00158   15        11           6,957 
113_0     1      X    11           0.00157   11        11           6,984 
57_1      0      X    11           0.00133   18        11           8,242 
69_1      1      X    11           0.00129   13        11           8,512 
103_1     1      X    11           0.00121   14        11           9,111 
45_1      0      X    11           4.869E-04 16        11           22,594
========= ====== ==== ============ ========= ========= ============ ======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
X    0.09979   426   
==== ========= ======

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
SourceReader       1.28500 0.36238 1.02876 1.54124 2      
preclassical       0.00615 0.00150 0.00331 0.00844 21     
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
calc_6650              time_sec memory_mb counts
====================== ======== ========= ======
total SourceReader     2.57000  2.00781   2     
composite source model 1.58320  3.01953   1     
total preclassical     0.12911  0.25781   21    
aggregate curves       0.00666  0.0       21    
store source_info      0.00394  0.0       1     
====================== ======== ========= ======