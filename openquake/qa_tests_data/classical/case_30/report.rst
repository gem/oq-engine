Classical PSHA for the southern Pacific Islands reduced
=======================================================

============== ===================
checksum32     1,406,686,210      
date           2019-10-01T06:32:41
engine_version 3.8.0-git66affb82eb
============== ===================

num_sites = 5, num_levels = 20, num_rlzs = 12

Parameters
----------
=============================== ==================
calculation_mode                'preclassical'    
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 300.0}
investigation_time              1.0               
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            5.0               
complex_fault_mesh_spacing      50.0              
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
======================= ============================
Name                    File                        
======================= ============================
gsim_logic_tree         `gmmLT_3.xml <gmmLT_3.xml>`_
job_ini                 `job.ini <job.ini>`_        
source_model_logic_tree `ssmLT.xml <ssmLT.xml>`_    
======================= ============================

Composite source model
----------------------
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
b1        1.00000 complex(4,3,0)  12              
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ======================================================================================= =========== ============================= ============================
grp_id gsims                                                                                   distances   siteparams                    ruptparams                  
====== ======================================================================================= =========== ============================= ============================
0      '[BooreAtkinson2008]' '[CampbellBozorgnia2008]' '[ChiouYoungs2008]' '[ZhaoEtAl2006Asc]' rjb rrup rx vs30 vs30measured z1pt0 z2pt5 dip hypo_depth mag rake ztor
1      '[BooreAtkinson2008]' '[CampbellBozorgnia2008]' '[ChiouYoungs2008]' '[ZhaoEtAl2006Asc]' rjb rrup rx vs30 vs30measured z1pt0 z2pt5 dip hypo_depth mag rake ztor
2      '[AtkinsonBoore2003SInter]' '[YoungsEtAl1997SInter]' '[ZhaoEtAl2006SInter]'             rrup        vs30                          hypo_depth mag              
====== ======================================================================================= =========== ============================= ============================

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=41, rlzs=12)>

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      25        3,800        1,100       
1      9.00000   1,117        1,117       
2      5.00000   3,536        3,536       
====== ========= ============ ============

Slowest sources
---------------
========== ====== ==== ============ ========= ========= ============ =======
source_id  grp_id code num_ruptures calc_time num_sites eff_ruptures speed  
========== ====== ==== ============ ========= ========= ============ =======
kt         2      C    3,536        0.01908   5.00000   3,536        185,303
sf_85      1      S    348          0.01861   3.00000   348          18,703 
sf_81      1      S    348          0.01673   3.00000   348          20,805 
sf_83      1      S    113          0.01533   1.00000   113          7,373  
sf_84      1      S    262          0.00919   1.00000   262          28,505 
sf_82      1      S    46           0.00684   1.00000   46           6,723  
ds_4_15201 0      P    100          0.00230   4.00000   100          43,473 
ds_4_19558 0      P    100          0.00168   1.00000   100          59,688 
ds_4_6534  0      P    100          0.00102   3.00000   100          97,769 
ds_4_18232 0      P    100          2.170E-04 3.00000   100          460,913
ds_4_36349 0      P    100          2.098E-04 1.00000   100          476,625
ds_4_464   0      P    100          1.810E-04 1.00000   100          552,609
ds_4_482   0      P    100          1.557E-04 1.00000   100          642,313
ds_4_5043  0      P    100          1.521E-04 2.00000   100          657,414
ds_4_2111  0      P    100          1.464E-04 1.00000   100          683,111
ds_4_8502  0      P    100          1.094E-04 4.00000   100          913,792
ds_4_8499  0      P    100          1.092E-04 4.00000   100          915,787
========== ====== ==== ============ ========= ========= ============ =======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
C    0.01908   1     
P    0.00628   38    
S    0.06669   5     
==== ========= ======

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
SourceReader       0.13521 0.16137 0.03386 0.32130 3      
preclassical       0.00823 0.00903 0.00162 0.02487 14     
================== ======= ======= ======= ======= =======

Data transfer
-------------
============ =========================================== =========
task         sent                                        received 
SourceReader apply_unc=5.56 KB ltmodel=804 B fname=359 B 140.38 KB
preclassical srcs=69.59 KB params=9.93 KB gsims=6.95 KB  4.78 KB  
============ =========================================== =========

Slowest operations
------------------
====================== ======== ========= ======
calc_6484              time_sec memory_mb counts
====================== ======== ========= ======
total SourceReader     0.40563  0.21484   3     
composite source model 0.34418  0.0       1     
total preclassical     0.11517  0.0       14    
aggregate curves       0.00343  0.0       14    
store source_info      0.00276  0.0       1     
====================== ======== ========= ======