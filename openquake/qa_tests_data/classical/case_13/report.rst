Classical PSHA QA test
======================

============== ===================
checksum32     752,446,534        
date           2019-05-10T05:07:58
engine_version 3.5.0-gitbaeb4c1e35
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
0      67_0      X    20,448 20,796 11           0.00325   21        50    
0      0_0       X    0      65     11           0.00299   11        36    
0      16_0      X    1,762  1,802  11           0.00298   1.00000   11    
0      29_0      X    5,250  5,402  11           0.00297   15        42    
0      7_0       X    30,662 30,710 11           0.00294   5.00000   24    
0      35_0      X    8,334  8,414  11           0.00289   18        46    
1      15_0      X    38,612 38,684 11           0.00256   19        47    
0      41_0      X    9,188  9,263  11           0.00201   4.00000   22    
0      73_0      X    25,842 26,238 11           0.00192   17        45    
1      98_0      X    50,470 50,518 11           0.00175   15        42    
1      72_0      X    47,128 47,188 11           0.00171   13        39    
0      22_0      X    2,854  2,989  11           0.00169   3.00000   19    
1      28_0      X    40,258 40,286 11           0.00164   5.00000   24    
1      113_0     X    34,588 34,800 11           0.00160   11        36    
1      34_0      X    40,970 41,144 11           0.00159   12        38    
1      85_0      X    48,850 48,874 11           0.00157   16        44    
1      91_0      X    49,724 49,768 11           0.00157   11        36    
1      79_0      X    48,010 48,080 11           0.00156   4.00000   22    
0      48_0      X    10,738 10,868 11           0.00153   7.00000   29    
1      21_0      X    39,556 39,581 11           0.00152   4.00000   22    
====== ========= ==== ====== ====== ============ ========= ========= ======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
X    0.09696   426   
==== ========= ======

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
read_source_models 1.16581 0.45238 0.84593 1.48570 2      
preclassical       0.00395 0.00130 0.00262 0.00665 31     
================== ======= ======= ======= ======= =======

Data transfer
-------------
================== ============================================================ ========
task               sent                                                         received
read_source_models converter=626 B fnames=234 B                                 1.46 MB 
preclassical       srcs=1.49 MB params=22.28 KB gsims=8.23 KB srcfilter=6.63 KB 26.08 KB
================== ============================================================ ========

Slowest operations
------------------
======================== ======== ========= ======
operation                time_sec memory_mb counts
======================== ======== ========= ======
total read_source_models 2.33163  1.50000   2     
total preclassical       0.12230  0.0       31    
managing sources         0.02450  0.0       1     
aggregate curves         0.00459  0.0       31    
store source_info        0.00234  0.0       1     
======================== ======== ========= ======