Classical PSHA for the southern Pacific Islands reduced
=======================================================

============== ===================
checksum32     1,406,686,210      
date           2019-10-01T06:08:43
engine_version 3.8.0-gite0871b5c35
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
5      9.00000   1,117        1,117       
2      5.00000   3,536        3,536       
====== ========= ============ ============

Slowest sources
---------------
========== ====== ==== ============ ========= ========= ============ =======
source_id  grp_id code num_ruptures calc_time num_sites eff_ruptures speed  
========== ====== ==== ============ ========= ========= ============ =======
sf_85      1      S    348          0.02667   3.00000   348          13,047 
sf_81      1      S    348          0.02348   3.00000   348          14,820 
kt         2      C    3,536        0.01369   5.00000   3,536        258,228
sf_83      1      S    113          0.00968   1.00000   113          11,679 
sf_82      1      S    46           0.00818   1.00000   46           5,623  
sf_84      1      S    262          0.00807   1.00000   262          32,484 
ds_4_18232 0      P    100          0.00186   3.00000   100          53,697 
ds_4_482   0      P    100          0.00169   1.00000   100          59,083 
ds_4_464   0      P    100          2.630E-04 1.00000   100          380,263
ds_4_5043  0      P    100          1.798E-04 2.00000   100          556,274
ds_4_15201 0      P    100          1.578E-04 4.00000   100          633,581
ds_4_19558 0      P    100          1.543E-04 1.00000   100          648,270
ds_4_36349 0      P    100          1.509E-04 1.00000   100          662,607
ds_4_6534  0      P    100          1.493E-04 3.00000   100          670,017
ds_4_8502  0      P    100          1.431E-04 4.00000   100          699,051
ds_4_8499  0      P    100          1.414E-04 4.00000   100          707,302
ds_4_2111  0      P    100          1.328E-04 1.00000   100          753,017
========== ====== ==== ============ ========= ========= ============ =======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
C    0.01369   1     
P    0.00503   38    
S    0.07608   5     
==== ========= ======

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
SourceReader       0.16757 0.18790 0.04744 0.38411 3      
preclassical       0.01505 0.01778 0.00311 0.04991 7      
================== ======= ======= ======= ======= =======

Data transfer
-------------
============ =========================================== =========
task         sent                                        received 
SourceReader apply_unc=5.46 KB ltmodel=804 B fname=338 B 140.36 KB
preclassical srcs=63.89 KB params=4.96 KB gsims=3.52 KB  2.77 KB  
============ =========================================== =========

Slowest operations
------------------
====================== ======== ========= ======
calc_23166             time_sec memory_mb counts
====================== ======== ========= ======
total SourceReader     0.50272  0.29688   3     
composite source model 0.40121  0.0       1     
total preclassical     0.10534  0.0       7     
aggregate curves       0.00269  0.0       7     
store source_info      0.00234  0.0       1     
====================== ======== ========= ======