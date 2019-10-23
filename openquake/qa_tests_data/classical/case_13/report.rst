Classical PSHA QA test
======================

============== ===================
checksum32     1,493,198,454      
date           2019-10-23T16:26:45
engine_version 3.8.0-git2e0d8e6795
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
0      1.15015   1,980        1,958       
1      0.93939   2,706        2,310       
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
113_0     1      X    11           0.00141   1.00000   11          
0_0       0      X    11           0.00131   1.00000   11          
86_0      0      X    11           0.00129   1.36364   11          
103_1     1      X    11           0.00129   1.27273   11          
4_1       1      X    11           0.00129   1.36364   11          
69_1      1      X    11           0.00128   1.18182   11          
29_0      0      X    11           0.00128   1.36364   11          
30_1      1      X    11           0.00128   0.72727   11          
19_1      0      X    11           0.00128   0.54545   11          
76_1      0      X    11           0.00128   1.90909   11          
98_0      1      X    11           0.00127   1.36364   11          
79_0      1      X    11           0.00127   0.36364   11          
21_0      1      X    11           0.00125   0.36364   11          
67_0      0      X    11           0.00125   1.90909   11          
48_0      0      X    11           0.00124   0.63636   11          
122_1     1      X    11           0.00124   1.18182   11          
38_1      0      X    11           0.00123   1.27273   11          
88_1      1      X    11           0.00113   1.90909   11          
57_1      0      X    11           0.00113   1.63636   11          
42_1      0      X    11           8.118E-04 0.09091   11          
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
X    0.05593  
==== =========

Information about the tasks
---------------------------
================== ======= ========= ======= ======= =======
operation-duration mean    stddev    min     max     outputs
SourceReader       2.23625 0.97158   1.54924 2.92326 2      
preclassical       0.00346 3.910E-04 0.00201 0.00421 21     
================== ======= ========= ======= ======= =======

Data transfer
-------------
============ =========================================== ========
task         sent                                        received
SourceReader apply_unc=8.36 KB ltmodel=434 B fname=228 B 2.11 MB 
preclassical srcs=1.48 MB params=16.75 KB gsims=5.58 KB  22.96 KB
============ =========================================== ========

Slowest operations
------------------
====================== ======== ========= ======
calc_44551             time_sec memory_mb counts
====================== ======== ========= ======
total SourceReader     4.47250  1.82422   2     
composite source model 2.96235  1.02734   1     
total preclassical     0.07268  0.51172   21    
aggregate curves       0.00506  0.0       21    
store source_info      0.00414  0.0       1     
====================== ======== ========= ======