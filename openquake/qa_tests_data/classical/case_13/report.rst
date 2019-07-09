Classical PSHA QA test
======================

============== ===================
checksum32     752,446,534        
date           2019-06-24T15:34:17
engine_version 3.6.0-git4b6205639c
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
====== ========= ==== ====== ====== ============ ========= ========= ====== =============
grp_id source_id code gidx1  gidx2  num_ruptures calc_time num_sites weight checksum     
====== ========= ==== ====== ====== ============ ========= ========= ====== =============
0      37_1      X    8,674  8,724  11           0.00366   16        17     2,564,204,816
0      41_1      X    9,263  9,338  11           0.00257   4.00000   14     636,945,679  
0      0_0       X    0      65     11           0.00257   11        16     3,964,529,887
1      22_1      X    39,641 39,676 11           0.00253   5.00000   14     4,128,466,209
1      117_0     X    35,776 36,166 11           0.00252   13        16     2,150,772,394
1      13_0      X    38,084 38,216 11           0.00252   3.00000   13     3,104,553,992
1      108_1     X    33,457 33,542 11           0.00251   17        17     3,750,215,950
1      47_0      X    43,116 43,200 11           0.00200   7.00000   15     2,408,156,638
1      60_1      X    45,800 45,830 11           0.00166   2.00000   12     1,981,744,293
1      56_1      X    45,100 45,150 11           0.00157   4.00000   14     930,519,689  
1      75_1      X    47,600 47,632 11           0.00156   10        16     1,327,591,891
1      70_0      X    46,884 46,928 11           0.00152   13        16     975,626,727  
1      99_0      X    50,566 50,656 11           0.00143   14        16     3,207,846,152
1      66_0      X    46,338 46,368 11           0.00136   12        16     2,785,160,391
1      51_0      X    44,152 44,220 11           0.00135   8.00000   15     4,090,373,943
1      28_0      X    40,258 40,286 11           0.00133   5.00000   14     492,354,978  
1      85_0      X    48,850 48,874 11           0.00124   16        17     1,513,866,974
1      32_0      X    40,770 40,798 11           0.00108   15        16     1,151,972,070
0      1_1       X    2,486  2,526  11           4.494E-04 9.00000   15     1,731,876,501
1      0_0       X    32,398 32,426 11           2.935E-04 9.00000   15     4,097,783,489
====== ========= ==== ====== ====== ============ ========= ========= ====== =============

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
X    0.09095   426   
==== ========= ======

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
preclassical       0.00605 0.00268 0.00246 0.01412 21     
read_source_models 1.28415 0.36944 1.02292 1.54538 2      
================== ======= ======= ======= ======= =======

Data transfer
-------------
================== ============================================================ ========
task               sent                                                         received
preclassical       srcs=1.48 MB params=15.09 KB gsims=5.58 KB srcfilter=4.51 KB 23.24 KB
read_source_models converter=626 B fnames=234 B                                 1.46 MB 
================== ============================================================ ========

Slowest operations
------------------
======================== ======== ========= ======
operation                time_sec memory_mb counts
======================== ======== ========= ======
total read_source_models 2.56830  1.73047   2     
total preclassical       0.12710  0.0       21    
managing sources         0.02278  0.0       1     
aggregate curves         0.00477  0.0       21    
store source_info        0.00213  0.0       1     
======================== ======== ========= ======