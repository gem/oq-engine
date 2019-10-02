Classical PSHA for the southern Pacific Islands reduced
=======================================================

============== ===================
checksum32     1,406,686,210      
date           2019-10-02T10:07:34
engine_version 3.8.0-git6f03622c6e
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
========== ====== ==== ============ ========= ========= ============
source_id  grp_id code num_ruptures calc_time num_sites eff_ruptures
========== ====== ==== ============ ========= ========= ============
sf_81      1      S    348          0.02064   0.00862   348         
kt         2      C    3,536        0.02007   0.00141   3,536       
sf_85      1      S    348          0.01919   0.00862   348         
sf_83      1      S    113          0.01753   0.00885   113         
sf_84      1      S    262          0.01044   0.00382   262         
sf_82      1      S    46           0.00672   0.02174   46          
ds_4_15201 0      P    100          0.00160   0.04000   100         
ds_4_19558 0      P    100          0.00143   0.01000   100         
ds_4_6534  0      P    100          0.00116   0.03000   100         
ds_4_482   0      P    100          3.123E-04 0.01000   100         
ds_4_464   0      P    100          3.057E-04 0.01000   100         
ds_4_5043  0      P    100          2.637E-04 0.02000   100         
ds_4_36349 0      P    100          2.370E-04 0.01000   100         
ds_4_18232 0      P    100          1.504E-04 0.03000   100         
ds_4_8499  0      P    100          1.235E-04 0.04000   100         
ds_4_8502  0      P    100          1.233E-04 0.04000   100         
ds_4_2111  0      P    100          1.135E-04 0.01000   100         
========== ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
C    0.02007   1     
P    0.00582   38    
S    0.07451   5     
==== ========= ======

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
SourceReader       0.15736 0.17141 0.05445 0.35523 3      
preclassical       0.00898 0.01015 0.00176 0.02838 14     
================== ======= ======= ======= ======= =======

Data transfer
-------------
============ =========================================== =========
task         sent                                        received 
SourceReader apply_unc=5.56 KB ltmodel=804 B fname=359 B 144.96 KB
preclassical srcs=69.59 KB params=9.93 KB gsims=6.95 KB  4.78 KB  
============ =========================================== =========

Slowest operations
------------------
====================== ======== ========= ======
calc_29526             time_sec memory_mb counts
====================== ======== ========= ======
total SourceReader     0.47208  0.64844   3     
composite source model 0.37860  0.0       1     
total preclassical     0.12571  0.0       14    
aggregate curves       0.00371  0.0       14    
store source_info      0.00273  0.0       1     
====================== ======== ========= ======