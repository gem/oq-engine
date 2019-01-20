Event Based Risk Lisbon
=======================

============== ===================
checksum32     2,870,861,887      
date           2019-01-20T07:39:05
engine_version 3.4.0-git452d0c6835
============== ===================

num_sites = 1, num_levels = 40

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
b1        0.60000 complex(2,2)    4/4             
b2        0.40000 complex(2,2)    4/4             
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ===================================== ========= ========== ==========
grp_id gsims                                 distances siteparams ruptparams
====== ===================================== ========= ========== ==========
0      AkkarBommer2010() AtkinsonBoore2006() rjb rrup  vs30       mag rake  
1      AkkarBommer2010() AtkinsonBoore2006() rjb rrup  vs30       mag rake  
2      AkkarBommer2010() AtkinsonBoore2006() rjb rrup  vs30       mag rake  
3      AkkarBommer2010() AtkinsonBoore2006() rjb rrup  vs30       mag rake  
====== ===================================== ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=8, rlzs=8)
  0,AkkarBommer2010(): [2 3]
  0,AtkinsonBoore2006(): [0 1]
  1,AkkarBommer2010(): [1 3]
  1,AtkinsonBoore2006(): [0 2]
  2,AkkarBommer2010(): [6 7]
  2,AtkinsonBoore2006(): [4 5]
  3,AkkarBommer2010(): [5 7]
  3,AtkinsonBoore2006(): [4 6]>

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
1 asset(s) x 8 realization(s) x 1 loss type(s) x 1 losses x 8 bytes x 16 tasks = 1 KB

Exposure model
--------------
=============== ========
#assets         1       
#taxonomies     1       
deductibile     absolute
insurance_limit absolute
=============== ========

======== ======= ====== === === ========= ==========
taxonomy mean    stddev min max num_sites num_assets
M1_2_PC  1.00000 NaN    1   1   1         1         
======== ======= ====== === === ========= ==========

Slowest sources
---------------
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= =======
grp_id source_id code gidx1 gidx2 num_ruptures calc_time split_time num_sites num_split weight 
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= =======
0      0         A    0     4     6,075        1.52008   0.0        1.00000   1         2.00000
0      1         A    4     8     989          0.42949   0.0        1.00000   1         2.00000
0      2         A    8     12    4,901        1.30638   0.0        1.00000   1         2.00000
1      10        A    12    16    1,116        0.37781   0.0        1.00000   1         0.0    
1      3         A    16    20    812          0.20075   0.0        1.00000   1         2.00000
1      4         A    20    24    310          0.17339   0.0        1.00000   1         0.0    
1      5         A    24    28    551          0.15925   0.0        1.00000   1         0.0    
1      6         A    28    32    1,054        0.25546   0.0        1.00000   1         0.0    
1      7         A    32    36    429          0.11417   0.0        1.00000   1         2.00000
1      8         A    36    40    342          0.09187   0.0        1.00000   1         0.0    
1      9         A    40    44    612          0.15917   0.0        1.00000   1         2.00000
2      0         A    44    48    6,075        1.44473   0.0        1.00000   1         2.00000
2      1         A    48    52    989          0.25311   0.0        1.00000   1         2.00000
2      2         A    52    56    4,901        1.30817   0.0        1.00000   1         2.00000
3      10        A    56    60    1,116        0.28853   0.0        1.00000   1         2.00000
3      3         A    60    64    812          0.20655   0.0        1.00000   1         0.0    
3      4         A    64    68    310          0.08851   0.0        1.00000   1         0.0    
3      5         A    68    72    551          0.14682   0.0        1.00000   1         2.00000
3      6         A    72    76    1,054        0.25928   0.0        1.00000   1         2.00000
3      7         A    76    80    429          0.11157   0.0        1.00000   1         0.0    
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= =======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
A    9.14131   22    
==== ========= ======

Duplicated sources
------------------
['0', '1', '10', '2', '3', '4', '5', '6', '7', '8', '9']
Found 11 source(s) with the same ID and 11 true duplicate(s)

Information about the tasks
---------------------------
================== ========= ========= ========= ======= =======
operation-duration mean      stddev    min       max     outputs
read_source_models 0.12114   7.806E-05 0.12108   0.12119 2      
split_filter       0.00284   3.277E-04 0.00249   0.00324 5      
sample_ruptures    0.76255   0.47987   0.25380   1.52081 12     
get_eid_rlz        6.723E-04 2.911E-04 3.636E-04 0.00125 14     
================== ========= ========= ========= ======= =======

Data transfer
-------------
================== ======================================= ========
task               sent                                    received
read_source_models converter=776 B fnames=232 B            20.3 KB 
split_filter       srcs=23 KB srcfilter=1.24 KB dummy=70 B 23.74 KB
sample_ruptures    param=48.27 KB sources=32.32 KB         13.69 KB
get_eid_rlz        self=22.29 KB                           4.43 KB 
================== ======================================= ========

Slowest operations
------------------
======================== ========= ========= ======
operation                time_sec  memory_mb counts
======================== ========= ========= ======
total sample_ruptures    9.15066   6.49219   12    
iter_ruptures            9.08899   0.0       22    
total read_source_models 0.24228   0.60547   2     
saving ruptures          0.03925   0.0       10    
total only_filter        0.01419   1.44922   5     
total get_eid_rlz        0.00941   0.30078   14    
store source model       0.00495   0.0       2     
store source_info        0.00327   0.0       1     
reading exposure         5.786E-04 0.0       1     
======================== ========= ========= ======