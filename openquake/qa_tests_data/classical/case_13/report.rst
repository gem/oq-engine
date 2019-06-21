Classical PSHA QA test
======================

============== ===================
checksum32     752,446,534        
date           2019-06-21T09:42:41
engine_version 3.6.0-git17fd0581aa
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
0      71_0      X    23,912 24,397 11           0.00791   19        17    
0      0_0       X    0      65     11           0.00257   11        16    
0      19_1      X    2,291  2,446  11           0.00253   6.00000   14    
0      57_1      X    14,400 14,710 11           0.00251   18        17    
0      38_1      X    8,824  8,924  11           0.00250   14        16    
0      76_1      X    28,878 29,362 11           0.00245   21        17    
1      21_0      X    39,556 39,581 11           0.00212   4.00000   14    
0      48_0      X    10,738 10,868 11           0.00176   7.00000   15    
1      103_1     X    32,868 32,910 11           0.00174   14        16    
0      67_0      X    20,448 20,796 11           0.00164   21        17    
1      122_1     X    37,840 38,020 11           0.00157   13        16    
1      113_0     X    34,588 34,800 11           0.00153   11        16    
1      79_0      X    48,010 48,080 11           0.00138   4.00000   14    
1      98_0      X    50,470 50,518 11           0.00136   15        16    
1      4_1       X    43,746 43,856 11           0.00136   15        16    
0      29_0      X    5,250  5,402  11           0.00134   15        16    
1      69_1      X    46,680 46,728 11           0.00132   13        16    
0      86_0      X    31,568 31,580 11           0.00127   15        16    
1      30_1      X    40,598 40,650 11           0.00114   8.00000   15    
1      88_1      X    49,071 49,148 11           0.00108   21        17    
====== ========= ==== ====== ====== ============ ========= ========= ======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
X    0.09234   426   
==== ========= ======

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
preclassical       0.00559 0.00251 0.00222 0.01317 21     
read_source_models 1.25405 0.42837 0.95115 1.55696 2      
================== ======= ======= ======= ======= =======

Data transfer
-------------
================== ============================================================ ========
task               sent                                                         received
preclassical       srcs=1.48 MB params=15.09 KB gsims=5.58 KB srcfilter=4.51 KB 23.14 KB
read_source_models converter=626 B fnames=234 B                                 1.46 MB 
================== ============================================================ ========

Slowest operations
------------------
======================== ======== ========= ======
operation                time_sec memory_mb counts
======================== ======== ========= ======
total read_source_models 2.50810  2.00391   2     
total preclassical       0.11747  0.0       21    
managing sources         0.02102  0.04297   1     
aggregate curves         0.00542  0.0       21    
store source_info        0.00338  0.0       1     
======================== ======== ========= ======