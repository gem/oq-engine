Event Based Risk Lisbon
=======================

============== ===================
checksum32     1,182,973,928      
date           2019-06-24T15:34:02
engine_version 3.6.0-git4b6205639c
============== ===================

num_sites = 1, num_levels = 40, num_rlzs = 8

Parameters
----------
=============================== ==================
calculation_mode                'event_based_risk'
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 400.0}
investigation_time              5.0               
ses_per_logic_tree_path         1                 
truncation_level                5.0               
rupture_mesh_spacing            4.0               
complex_fault_mesh_spacing      4.0               
width_of_mfd_bin                0.1               
area_source_discretization      20.0              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     23                
master_seed                     42                
ses_seed                        42                
avg_losses                      True              
=============================== ==================

Input files
-----------
======================== ============================================================
Name                     File                                                        
======================== ============================================================
exposure                 `exposure_model_1asset.xml <exposure_model_1asset.xml>`_    
gsim_logic_tree          `gsim_logic_tree.xml <gsim_logic_tree.xml>`_                
job_ini                  `job.ini <job.ini>`_                                        
source_model_logic_tree  `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
structural_vulnerability `vulnerability_model2013.xml <vulnerability_model2013.xml>`_
======================== ============================================================

Composite source model
----------------------
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
b1        0.60000 complex(2,2)    4               
b2        0.40000 complex(2,2)    4               
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ========================================= ========= ========== ==========
grp_id gsims                                     distances siteparams ruptparams
====== ========================================= ========= ========== ==========
0      '[AkkarBommer2010]' '[AtkinsonBoore2006]' rjb rrup  vs30       mag rake  
1      '[AkkarBommer2010]' '[AtkinsonBoore2006]' rjb rrup  vs30       mag rake  
2      '[AkkarBommer2010]' '[AtkinsonBoore2006]' rjb rrup  vs30       mag rake  
3      '[AkkarBommer2010]' '[AtkinsonBoore2006]' rjb rrup  vs30       mag rake  
====== ========================================= ========= ========== ==========

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=16, rlzs=8)>

Number of ruptures per tectonic region type
-------------------------------------------
=================== ====== ==================== ============ ============
source_model        grp_id trt                  eff_ruptures tot_ruptures
=================== ====== ==================== ============ ============
SA_RA_CATAL1_00.xml 0      Active Shallow Crust 11,965       11,965      
SA_RA_CATAL1_00.xml 1      Stable Shallow Crust 5,226        5,226       
SA_RA_CATAL2_00.xml 2      Active Shallow Crust 11,965       11,965      
SA_RA_CATAL2_00.xml 3      Stable Shallow Crust 5,226        5,226       
=================== ====== ==================== ============ ============

============= ======
#TRT models   4     
#eff_ruptures 34,382
#tot_ruptures 34,382
#tot_weight   34,382
============= ======

Estimated data transfer for the avglosses
-----------------------------------------
1 asset(s) x 8 realization(s) x 1 loss type(s) losses x 8 bytes x 16 tasks = 1 KB

Exposure model
--------------
=========== =
#assets     1
#taxonomies 1
=========== =

======== ======= ====== === === ========= ==========
taxonomy mean    stddev min max num_sites num_assets
M1_2_PC  1.00000 NaN    1   1   1         1         
======== ======= ====== === === ========= ==========

Slowest sources
---------------
====== ========= ==== ===== ===== ============ ========= ========= ======= =============
grp_id source_id code gidx1 gidx2 num_ruptures calc_time num_sites weight  checksum     
====== ========= ==== ===== ===== ============ ========= ========= ======= =============
2      0         A    44    48    6,075        0.09533   0.0       2.00000 4,123,380,995
0      2         A    8     12    4,901        0.05861   0.0       2.00000 1,776,014,846
0      0         A    0     4     6,075        0.05547   0.0       2.00000 3,299,069,396
2      2         A    52    56    4,901        0.04864   0.0       2.00000 3,110,589,853
1      10        A    12    16    1,116        0.03833   0.0       0.0     3,033,052,789
0      1         A    4     8     989          0.03251   0.0       2.00000 671,069,602  
3      4         A    64    68    310          0.03085   0.0       0.0     3,608,920,371
3      10        A    56    60    1,116        0.02989   0.0       2.00000 994,359,215  
1      3         A    16    20    812          0.02504   0.0       2.00000 473,349,364  
3      3         A    60    64    812          0.02236   0.0       0.0     600,620,315  
3      9         A    84    88    612          0.01873   0.0       0.0     1,007,927,553
2      1         A    48    52    989          0.01849   0.0       2.00000 1,496,429,807
1      4         A    20    24    310          0.01758   0.0       0.0     1,024,376,825
1      9         A    40    44    612          0.01568   0.0       2.00000 3,527,721,311
3      8         A    80    84    342          0.01342   0.0       0.0     3,253,645,350
3      6         A    72    76    1,054        0.01271   0.0       2.00000 3,758,082,409
1      6         A    28    32    1,054        0.01260   0.0       0.0     558,943,275  
3      5         A    68    72    551          0.01058   0.0       2.00000 2,599,207,025
1      5         A    24    28    551          0.00984   0.0       0.0     2,342,598    
1      7         A    32    36    429          0.00982   0.0       2.00000 951,302,763  
====== ========= ==== ===== ===== ============ ========= ========= ======= =============

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
A    0.59284   22    
==== ========= ======

Information about the tasks
---------------------------
================== ========= ========= ========= ======= =======
operation-duration mean      stddev    min       max     outputs
get_eid_rlz        8.041E-04 2.863E-04 5.040E-04 0.00133 11     
read_source_models 0.16200   0.00788   0.15643   0.16757 2      
sample_ruptures    0.05342   0.02043   0.02141   0.09942 12     
================== ========= ========= ========= ======= =======

Data transfer
-------------
================== ================================================= ========
task               sent                                              received
get_eid_rlz        self=18.58 KB                                     3.47 KB 
read_source_models converter=626 B fnames=232 B                      20.88 KB
sample_ruptures    param=47.43 KB sources=31.58 KB srcfilter=2.58 KB 13.08 KB
================== ================================================= ========

Slowest operations
------------------
======================== ========= ========= ======
operation                time_sec  memory_mb counts
======================== ========= ========= ======
total sample_ruptures    0.64104   1.08984   12    
total read_source_models 0.32400   0.0       2     
saving ruptures          0.02579   0.0       10    
store source model       0.00978   0.0       2     
total get_eid_rlz        0.00885   0.0       11    
store source_info        0.00207   0.0       1     
reading exposure         6.039E-04 0.0       1     
======================== ========= ========= ======