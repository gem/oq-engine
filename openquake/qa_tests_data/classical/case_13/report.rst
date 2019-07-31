Classical PSHA QA test
======================

============== ===================
checksum32     752,446,534        
date           2019-07-30T15:04:17
engine_version 3.7.0-git3b3dff46da
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
bFault_stitched_D2.1_Char.xml 1      Active Shallow Crust 4,257        2,706       
============================= ====== ==================== ============ ============

============= =====
#TRT models   2    
#eff_ruptures 8,525
#tot_ruptures 4,686
============= =====

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ====== ======
source_id grp_id code num_ruptures calc_time num_sites weight speed 
========= ====== ==== ============ ========= ========= ====== ======
56_0      0      X    11           0.00303   30        22     7,250 
47_1      0      X    11           0.00229   14        22     9,602 
0_0       0      X    11           0.00210   20        22     10,457
30_1      0      X    11           0.00179   21        22     12,274
59_1      0      X    11           0.00179   21        22     12,295
100_0     1      X    11           0.00176   13        11     6,241 
9_1       0      X    11           0.00174   16        11     6,330 
44_0      0      X    11           0.00150   25        22     14,663
112_0     1      X    11           0.00145   11        11     7,576 
88_1      0      X    11           7.174E-04 26        22     30,666
59_0      0      X    11           4.339E-04 21        22     50,700
89_0      0      X    11           3.493E-04 26        22     62,986
35_1      0      X    11           3.238E-04 37        22     67,949
121_1     1      X    11           3.226E-04 8.00000   11     34,100
21_1      0      X    11           3.090E-04 7.00000   22     71,200
68_1      0      X    11           3.037E-04 25        22     72,429
0_1       0      X    11           2.878E-04 20        22     76,450
71_0      0      X    11           2.866E-04 29        22     76,768
64_0      0      X    11           2.811E-04 33        22     78,265
15_0      0      X    11           2.770E-04 15        22     79,410
========= ====== ==== ============ ========= ========= ====== ======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
X    0.06230   426   
==== ========= ======

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
preclassical       0.00855 0.00275 0.00224 0.01119 9      
read_source_models 1.62543 0.42300 1.32632 1.92454 2      
================== ======= ======= ======= ======= =======

Data transfer
-------------
================== =========================================================== ========
task               sent                                                        received
preclassical       srcs=1.47 MB params=6.82 KB gsims=2.39 KB srcfilter=1.93 KB 19.08 KB
read_source_models converter=628 B fnames=220 B                                1.46 MB 
================== =========================================================== ========

Slowest operations
------------------
======================== ======== ========= ======
calc_15524               time_sec memory_mb counts
======================== ======== ========= ======
total read_source_models 3.25086  2.25000   2     
total preclassical       0.07692  0.25781   9     
managing sources         0.01373  0.0       1     
aggregate curves         0.00333  0.0       9     
store source_info        0.00261  0.0       1     
======================== ======== ========= ======