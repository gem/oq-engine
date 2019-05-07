Classical PSHA QA test
======================

============== ===================
checksum32     752,446,534        
date           2019-05-03T06:44:10
engine_version 3.5.0-git7a6d15e809
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

  <RlzsAssoc(size=4, rlzs=4)
  0,'[BooreAtkinson2008]': [0]
  0,'[ChiouYoungs2008]': [1]
  1,'[BooreAtkinson2008]': [2]
  1,'[ChiouYoungs2008]': [3]>

Number of ruptures per tectonic region type
-------------------------------------------
============================= ====== ==================== ============ ============
source_model                  grp_id trt                  eff_ruptures tot_ruptures
============================= ====== ==================== ============ ============
aFault_aPriori_D2.1.xml       0      Active Shallow Crust 1,958        1,980       
bFault_stitched_D2.1_Char.xml 1      Active Shallow Crust 2,310        2,706       
============================= ====== ==================== ============ ============

============= =====
#TRT models   2    
#eff_ruptures 4,268
#tot_ruptures 4,686
#tot_weight   4,686
============= =====

Slowest sources
---------------
====== ========= ==== ====== ====== ============ ========= ========= ======
grp_id source_id code gidx1  gidx2  num_ruptures calc_time num_sites weight
====== ========= ==== ====== ====== ============ ========= ========= ======
1      60_0      X    45,770 45,800 11           1.304E-04 2.00000   15    
1      58_0      X    45,400 45,495 11           4.458E-05 4.00000   22    
1      85_0      X    48,850 48,874 11           2.670E-05 16        44    
0      35_0      X    8,334  8,414  11           2.480E-05 18        46    
0      48_0      X    10,738 10,868 11           2.408E-05 7.00000   29    
0      22_0      X    2,854  2,989  11           2.408E-05 3.00000   19    
0      29_0      X    5,250  5,402  11           2.384E-05 15        42    
0      60_0      X    16,062 16,274 11           2.265E-05 9.00000   33    
0      67_0      X    20,448 20,796 11           2.146E-05 21        50    
1      120_0     X    37,234 37,279 11           2.003E-05 8.00000   31    
0      0_0       X    0      65     11           1.907E-05 11        36    
0      0_1       X    65     130    11           1.812E-05 11        36    
0      41_0      X    9,188  9,263  11           1.669E-05 4.00000   22    
0      7_0       X    30,662 30,710 11           1.526E-05 5.00000   24    
1      107_0     X    33,300 33,336 11           1.478E-05 3.00000   19    
1      113_0     X    34,588 34,800 11           1.454E-05 11        36    
0      16_0      X    1,762  1,802  11           1.454E-05 1.00000   11    
0      54_0      X    12,964 13,139 11           1.335E-05 9.00000   33    
1      21_0      X    39,556 39,581 11           1.311E-05 4.00000   22    
0      86_0      X    31,568 31,580 11           1.311E-05 15        42    
====== ========= ==== ====== ====== ============ ========= ========= ======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
X    0.00224   426   
==== ========= ======

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
read_source_models 1.13614 0.35127 0.88775 1.38453 2      
preclassical       0.00406 0.00128 0.00252 0.00709 31     
================== ======= ======= ======= ======= =======

Data transfer
-------------
================== =========================================================== ========
task               sent                                                        received
read_source_models converter=626 B fnames=234 B                                1.46 MB 
preclassical       srcs=1.49 MB params=22.28 KB gsims=8.23 KB srcfilter=6.6 KB 25.66 KB
================== =========================================================== ========

Slowest operations
------------------
======================== ======== ========= ======
operation                time_sec memory_mb counts
======================== ======== ========= ======
total read_source_models 2.27228  1.87891   2     
total preclassical       0.12585  0.0       31    
managing sources         0.02769  0.0       1     
aggregate curves         0.00405  0.0       31    
store source_info        0.00316  0.0       1     
======================== ======== ========= ======