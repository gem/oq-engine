Classical PSHA for the southern Pacific Islands reduced
=======================================================

============== ===================
checksum32     1_406_686_210      
date           2020-03-13T11:22:39
engine_version 3.9.0-gitfb3ef3a732
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
pointsource_distance            {'default': {}}   
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
========= ======= ================
smlt_path weight  num_realizations
========= ======= ================
b1        1.00000 12              
========= ======= ================

Required parameters per tectonic region type
--------------------------------------------
====== ======================================================================================= =========== ============================= ============================
grp_id gsims                                                                                   distances   siteparams                    ruptparams                  
====== ======================================================================================= =========== ============================= ============================
0      '[BooreAtkinson2008]' '[CampbellBozorgnia2008]' '[ChiouYoungs2008]' '[ZhaoEtAl2006Asc]' rjb rrup rx vs30 vs30measured z1pt0 z2pt5 dip hypo_depth mag rake ztor
1      '[AtkinsonBoore2003SInter]' '[YoungsEtAl1997SInter]' '[ZhaoEtAl2006SInter]'             rrup        vs30                          hypo_depth mag              
====== ======================================================================================= =========== ============================= ============================

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      0.06811   4_917        2_217       
1      0.06929   3_536        3_536       
====== ========= ============ ============

Slowest sources
---------------
========== ====== ==== ============ ========= ========= ============
source_id  grp_id code num_ruptures calc_time num_sites eff_ruptures
========== ====== ==== ============ ========= ========= ============
sf_85      0      S    348          0.17091   0.12931   348         
sf_81      0      S    348          0.16530   0.12931   348         
sf_84      0      S    262          0.13771   0.05344   262         
sf_83      0      S    113          0.09459   0.10619   113         
sf_82      0      S    46           0.06869   0.21739   46          
kt         1      C    3_536        0.06501   0.06929   3_536       
ds_4_18232 0      P    100          1.338E-04 0.03000   100         
ds_4_5043  0      P    100          1.171E-04 0.02000   100         
ds_4_482   0      P    100          1.161E-04 0.01000   100         
ds_4_36349 0      P    100          1.159E-04 0.01000   100         
ds_4_464   0      P    100          1.156E-04 0.01000   100         
ds_4_6534  0      P    100          1.147E-04 0.03000   100         
ds_4_15201 0      P    100          1.099E-04 0.04000   100         
ds_4_8502  0      P    100          1.082E-04 0.04000   100         
ds_4_8499  0      P    100          1.061E-04 0.04000   100         
ds_4_19558 0      P    100          1.049E-04 0.01000   100         
ds_4_2111  0      P    100          9.942E-05 0.01000   100         
========== ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
C    0.06501  
P    0.00124  
S    0.63721  
==== =========

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
preclassical       0.90468 2.63098 0.00260 8.38924 10     
read_source_model  0.11933 0.15832 0.01576 0.30157 3      
================== ======= ======= ======= ======= =======

Data transfer
-------------
================= ========================================== ========
task              sent                                       received
read_source_model converter=996 B fname=338 B srcfilter=12 B 61.21 KB
preclassical      srcs=69.88 KB params=8.26 KB gsims=4.99 KB 3.88 KB 
================= ========================================== ========

Slowest operations
------------------
=========================== ======== ========= ======
calc_66994                  time_sec memory_mb counts
=========================== ======== ========= ======
total preclassical          9.04680  7.53906   10    
splitting/filtering sources 8.32419  6.54297   10    
composite source model      0.87944  0.0       1     
total read_source_model     0.35799  2.58203   3     
store source_info           0.00276  0.0       1     
aggregate curves            0.00241  0.0       9     
=========================== ======== ========= ======