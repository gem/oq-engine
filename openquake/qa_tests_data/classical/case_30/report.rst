Classical PSHA for the southern Pacific Islands reduced
=======================================================

============== ===================
checksum32     1,406,686,210      
date           2019-10-23T16:26:39
engine_version 3.8.0-git2e0d8e6795
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
0      0.02273   3,800        1,100       
1      0.00806   1,117        1,117       
2      0.00141   3,536        3,536       
====== ========= ============ ============

Slowest sources
---------------
========== ====== ==== ============ ========= ========= ============
source_id  grp_id code num_ruptures calc_time num_sites eff_ruptures
========== ====== ==== ============ ========= ========= ============
kt         2      C    3,536        0.01416   0.00141   3,536       
sf_85      1      S    348          0.01174   0.00862   348         
sf_81      1      S    348          0.01145   0.00862   348         
sf_84      1      S    262          0.01112   0.00382   262         
sf_83      1      S    113          0.00785   0.00885   113         
sf_82      1      S    46           0.00737   0.02174   46          
ds_4_18232 0      P    100          1.283E-04 0.03000   100         
ds_4_464   0      P    100          1.073E-04 0.01000   100         
ds_4_482   0      P    100          1.044E-04 0.01000   100         
ds_4_5043  0      P    100          1.018E-04 0.02000   100         
ds_4_6534  0      P    100          9.942E-05 0.03000   100         
ds_4_36349 0      P    100          9.823E-05 0.01000   100         
ds_4_19558 0      P    100          9.751E-05 0.01000   100         
ds_4_15201 0      P    100          9.727E-05 0.04000   100         
ds_4_8502  0      P    100          9.513E-05 0.04000   100         
ds_4_8499  0      P    100          9.251E-05 0.04000   100         
ds_4_2111  0      P    100          9.131E-05 0.01000   100         
========== ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
C    0.01416  
P    0.00111  
S    0.04953  
==== =========

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
SourceReader       0.21509 0.24532 0.04088 0.49564 3      
preclassical       0.00754 0.00591 0.00139 0.01553 10     
================== ======= ======= ======= ======= =======

Data transfer
-------------
============ =========================================== =========
task         sent                                        received 
SourceReader apply_unc=5.56 KB ltmodel=804 B fname=359 B 144.45 KB
preclassical srcs=66.04 KB params=7.49 KB gsims=4.99 KB  3.64 KB  
============ =========================================== =========

Slowest operations
------------------
====================== ======== ========= ======
calc_44540             time_sec memory_mb counts
====================== ======== ========= ======
total SourceReader     0.64528  0.53906   3     
composite source model 0.51071  0.0       1     
total preclassical     0.07536  0.0       10    
store source_info      0.00260  0.0       1     
aggregate curves       0.00220  0.0       10    
====================== ======== ========= ======