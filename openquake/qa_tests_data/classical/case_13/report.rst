Classical PSHA QA test
======================

============== ===================
checksum32     752,446,534        
date           2019-09-24T15:21:23
engine_version 3.7.0-git749bb363b3
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

Number of ruptures per tectonic region type
-------------------------------------------
============================= ====== ==================== ============ ============
source_model                  grp_id trt                  eff_ruptures tot_ruptures
============================= ====== ==================== ============ ============
aFault_aPriori_D2.1.xml       0      Active Shallow Crust 4,268        1,980       
bFault_stitched_D2.1_Char.xml 1      Active Shallow Crust 4,268        2,706       
============================= ====== ==================== ============ ============

============= =====
#TRT models   2    
#eff_ruptures 8,536
#tot_ruptures 4,686
============= =====

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============ ======
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures speed 
========= ====== ==== ============ ========= ========= ============ ======
0_0       0      X    11           5.820E-04 20        22           37,802
68_0      0      X    11           5.195E-04 25        22           42,347
34_0      0      X    11           4.721E-04 23        22           46,603
13_1      0      X    11           4.556E-04 23        22           48,286
49_0      0      X    11           4.482E-04 10        22           49,082
18_1      0      X    11           4.437E-04 26        22           49,583
0_1       0      X    11           4.420E-04 20        22           49,771
35_1      0      X    11           4.413E-04 37        22           49,851
47_1      0      X    11           4.311E-04 14        22           51,037
87_0      0      X    11           4.287E-04 26        22           51,321
10_0      0      X    11           4.249E-04 25        22           51,782
23_0      0      X    11           4.179E-04 20        22           52,638
47_0      0      X    11           4.163E-04 14        22           52,849
14_0      0      X    11           4.151E-04 17        22           53,001
68_1      0      X    11           4.141E-04 25        22           53,123
27_0      0      X    11           4.106E-04 28        22           53,586
72_0      0      X    11           4.058E-04 26        22           54,215
10_1      0      X    11           4.051E-04 25        22           54,311
24_0      0      X    11           4.022E-04 15        22           54,698
53_0      0      X    11           4.015E-04 29        22           54,795
========= ====== ==== ============ ========= ========= ============ ======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
X    0.06111   426   
==== ========= ======

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
preclassical       0.00401 0.00125 0.00117 0.00549 21     
read_source_models 1.22736 0.39575 0.94752 1.50719 2      
================== ======= ======= ======= ======= =======

Data transfer
-------------
================== =============================================== ========
task               sent                                            received
preclassical       srcs=1.48 MB srcfilter=32.28 KB params=15.89 KB 22.82 KB
read_source_models converter=628 B fnames=234 B                    1.46 MB 
================== =============================================== ========

Slowest operations
------------------
======================== ======== ========= ======
calc_1842                time_sec memory_mb counts
======================== ======== ========= ======
total read_source_models 2.45471  2.10547   2     
total preclassical       0.08424  0.0       21    
aggregate curves         0.00598  0.0       21    
store source_info        0.00319  0.0       1     
managing sources         0.00213  0.0       1     
======================== ======== ========= ======