Classical PSHA for the southern Pacific Islands reduced
=======================================================

============== ===================
checksum32     1_406_686_210      
date           2020-01-16T05:31:38
engine_version 3.8.0-git83c45f7244
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
pointsource_distance            None              
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
0      0.02273   3_800        1_100       
1      0.11280   1_117        1_117       
2      0.06929   3_536        3_536       
====== ========= ============ ============

Slowest sources
---------------
========== ====== ==== ============ ========= ========= ============
source_id  grp_id code num_ruptures calc_time num_sites eff_ruptures
========== ====== ==== ============ ========= ========= ============
sf_85      1      S    348          0.16877   0.12931   348         
sf_81      1      S    348          0.16868   0.12931   348         
sf_84      1      S    262          0.15752   0.05344   262         
sf_83      1      S    113          0.09546   0.10619   113         
sf_82      1      S    46           0.07210   0.21739   46          
kt         2      C    3_536        0.06375   0.06929   3_536       
ds_4_18232 0      P    100          2.866E-04 0.03000   100         
ds_4_464   0      P    100          2.694E-04 0.01000   100         
ds_4_482   0      P    100          2.670E-04 0.01000   100         
ds_4_5043  0      P    100          2.553E-04 0.02000   100         
ds_4_6534  0      P    100          2.496E-04 0.03000   100         
ds_4_8502  0      P    100          2.415E-04 0.04000   100         
ds_4_8499  0      P    100          2.408E-04 0.04000   100         
ds_4_36349 0      P    100          2.310E-04 0.01000   100         
ds_4_19558 0      P    100          2.306E-04 0.01000   100         
ds_4_2111  0      P    100          2.151E-04 0.01000   100         
ds_4_15201 0      P    100          1.109E-04 0.04000   100         
========== ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
C    0.06375  
P    0.00260  
S    0.66253  
==== =========

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
SourceReader       0.14885 0.18449 0.01567 0.35943 3      
preclassical       0.90433 2.61800 0.00267 8.35174 10     
================== ======= ======= ======= ======= =======

Data transfer
-------------
============ =========================================== ========
task         sent                                        received
SourceReader apply_unc=5.56 KB ltmodel=804 B fname=359 B 70.8 KB 
preclassical srcs=66.48 KB params=8.51 KB gsims=4.99 KB  3.87 KB 
============ =========================================== ========

Slowest operations
------------------
=========================== ======== ========= ======
calc_43324                  time_sec memory_mb counts
=========================== ======== ========= ======
total preclassical          9.04328  0.0       10    
splitting/filtering sources 8.28893  0.0       10    
total SourceReader          0.44654  0.35938   3     
composite source model      0.38283  0.0       1     
store source_info           0.00250  0.0       1     
aggregate curves            0.00244  0.0       9     
=========================== ======== ========= ======