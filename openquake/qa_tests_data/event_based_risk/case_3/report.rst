Event Based Risk Lisbon
=======================

============== ===================
checksum32     3,187,009,563      
date           2018-09-25T14:28:35
engine_version 3.3.0-git8ffb37de56
============== ===================

num_sites = 1, num_levels = 40

Parameters
----------
=============================== ==================
calculation_mode                'event_based_risk'
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 400.0}
investigation_time              2.0               
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
source                   `SA_RA_CATAL1_00.xml <SA_RA_CATAL1_00.xml>`_                
source                   `SA_RA_CATAL2_00.xml <SA_RA_CATAL2_00.xml>`_                
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
SA_RA_CATAL1_00.xml 0      Active Shallow Crust 10,370       11,965      
SA_RA_CATAL1_00.xml 1      Stable Shallow Crust 5,202        5,226       
SA_RA_CATAL2_00.xml 2      Active Shallow Crust 10,370       11,965      
SA_RA_CATAL2_00.xml 3      Stable Shallow Crust 5,202        5,226       
=================== ====== ==================== ============ ============

============= ======
#TRT models   4     
#eff_ruptures 31,144
#tot_ruptures 34,382
#tot_weight   0     
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
0      0         A    0     4     6,075        4.42245   5.79192    135       135       1.00000
0      1         A    4     8     989          0.75045   0.39050    43        43        0.0    
0      2         A    8     12    4,901        2.55093   4.79858    114       114       1.00000
1      10        A    12    16    1,116        0.86993   1.11586    62        62        0.0    
1      3         A    16    20    812          0.61249   0.17307    28        28        0.0    
1      4         A    20    24    310          0.23999   0.41822    31        31        0.0    
1      5         A    24    28    551          0.42749   0.16641    19        19        1.00000
1      6         A    28    32    1,054        0.63469   0.35121    34        34        0.0    
1      7         A    32    36    429          0.33442   0.22789    33        33        0.0    
1      8         A    36    40    342          0.25142   0.11328    19        19        0.0    
1      9         A    40    44    612          0.25304   0.84085    49        49        0.0    
2      0         A    0     4     6,075        4.33737   5.38757    135       135       2.00000
2      1         A    4     8     989          0.77659   0.41869    43        43        4.00000
2      2         A    8     12    4,901        2.36381   4.89020    114       114       1.00000
3      10        A    12    16    1,116        0.90063   1.19633    62        62        0.0    
3      3         A    16    20    812          0.38891   0.18563    28        28        0.0    
3      4         A    20    24    310          0.25447   0.44448    31        31        2.00000
3      5         A    24    28    551          0.41774   0.17919    19        19        0.0    
3      6         A    28    32    1,054        0.77349   0.37663    34        34        0.0    
3      7         A    32    36    429          0.33208   0.25205    33        33        1.00000
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= =======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
A    22        22    
==== ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =========
operation-duration mean    stddev  min     max     num_tasks
read_source_models 0.16752 0.01211 0.15896 0.17608 2        
split_filter       0.09528 0.05320 0.02308 0.15229 5        
build_ruptures     1.25853 0.32931 0.56404 1.52989 18       
compute_gmfs       0.01897 0.00874 0.01085 0.03029 4        
================== ======= ======= ======= ======= =========

Data transfer
-------------
================== ================================================================================================= =========
task               sent                                                                                              received 
read_source_models monitor=736 B converter=638 B fnames=382 B                                                        20.26 KB 
split_filter       srcs=158.07 KB monitor=1.86 KB srcfilter=1.07 KB sample_factor=105 B seed=70 B                    424.1 KB 
build_ruptures     srcs=435.57 KB param=8.19 KB monitor=6.73 KB srcfilter=3.87 KB                                    569.94 KB
compute_gmfs       sources_or_ruptures=26.07 KB param=16.48 KB rlzs_by_gsim=1.66 KB monitor=1.35 KB src_filter=880 B 20.22 KB 
================== ================================================================================================= =========

Slowest operations
------------------
======================== ========= ========= ======
operation                time_sec  memory_mb counts
======================== ========= ========= ======
total build_ruptures     22        0.0       18    
total split_filter       0.47640   0.25391   5     
total read_source_models 0.33504   0.0       2     
updating source_info     0.17364   0.0       1     
total compute_gmfs       0.07587   0.15625   4     
building hazard          0.05244   0.15625   4     
saving ruptures          0.03386   0.0       13    
building ruptures        0.01445   0.0       4     
making contexts          0.01374   0.0       15    
store source_info        0.00673   0.0       1     
managing sources         0.00661   0.0       1     
saving gmfs              0.00632   0.0       4     
GmfGetter.init           0.00489   0.0       4     
building riskinputs      0.00304   0.0       1     
setting event years      0.00124   0.0       1     
saving gmf_data/indices  9.582E-04 0.0       1     
aggregating hcurves      6.659E-04 0.0       4     
reading exposure         5.131E-04 0.0       1     
======================== ========= ========= ======