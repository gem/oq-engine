Classical PSHA for the southern Pacific Islands reduced
=======================================================

============== ===================
checksum32     1,406,686,210      
date           2019-10-01T07:01:12
engine_version 3.8.0-gitbd71c2f960
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
kt         2      C    3,536        0.02033   5.00000   3,536        173,892
sf_85      1      S    348          0.01670   3.00000   348          20,839 
sf_83      1      S    113          0.01591   1.00000   113          7,102  
sf_81      1      S    348          0.01397   3.00000   348          24,909 
sf_84      1      S    262          0.00941   1.00000   262          27,851 
sf_82      1      S    46           0.00657   1.00000   46           7,004  
ds_4_15201 0      P    100          0.00252   4.00000   100          39,734 
ds_4_6534  0      P    100          0.00169   3.00000   100          59,116 
ds_4_19558 0      P    100          0.00135   1.00000   100          74,026 
ds_4_18232 0      P    100          2.434E-04 3.00000   100          410,804
ds_4_36349 0      P    100          2.232E-04 1.00000   100          448,109
ds_4_464   0      P    100          2.005E-04 1.00000   100          498,728
ds_4_482   0      P    100          1.791E-04 1.00000   100          558,496
ds_4_5043  0      P    100          1.688E-04 2.00000   100          592,416
ds_4_8499  0      P    100          1.640E-04 4.00000   100          609,637
ds_4_8502  0      P    100          1.633E-04 4.00000   100          612,307
ds_4_2111  0      P    100          1.154E-04 1.00000   100          866,592
========== ====== ==== ============ ========= ========= ============ =======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
C    0.02033   1     
P    0.00702   38    
S    0.06256   5     
==== ========= ======

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
SourceReader       0.14122 0.16986 0.03471 0.33710 3      
preclassical       0.00803 0.00873 0.00190 0.02563 14     
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
calc_6639              time_sec memory_mb counts
====================== ======== ========= ======
total SourceReader     0.42365  0.32812   3     
composite source model 0.35866  0.0       1     
total preclassical     0.11238  0.0       14    
aggregate curves       0.00380  0.0       14    
store source_info      0.00262  0.0       1     
====================== ======== ========= ======