Event Based Risk Lisbon
=======================

============== ===================
checksum32     3,187,009,563      
date           2018-10-04T15:36:48
engine_version 3.3.0-gitf22d3f2c70
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
#tot_weight   3,114 
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
0      0         A    0     4     6,075        3.57633   10         135       135       1.00000
0      1         A    4     8     989          0.67516   0.39396    43        43        0.0    
0      2         A    8     12    4,901        1.91351   4.28021    114       114       1.00000
1      10        A    12    16    1,116        0.77944   1.02231    62        62        0.0    
1      3         A    16    20    812          0.42991   0.15304    28        28        0.0    
1      4         A    20    24    310          0.21078   0.37554    31        31        0.0    
1      5         A    24    28    551          0.28097   0.15100    19        19        1.00000
1      6         A    28    32    1,054        0.38572   0.31598    34        34        0.0    
1      7         A    32    36    429          0.28400   0.20604    33        33        0.0    
1      8         A    36    40    342          0.23824   0.09975    19        19        0.0    
1      9         A    40    44    612          0.39723   0.87475    49        49        0.0    
2      0         A    0     4     6,075        3.74127   4.62324    135       135       2.00000
2      1         A    4     8     989          0.55524   0.35457    43        43        4.00000
2      2         A    8     12    4,901        2.09716   8.12304    114       114       1.00000
3      10        A    12    16    1,116        0.44870   1.50331    62        62        0.0    
3      3         A    16    20    812          0.31324   0.17188    28        28        0.0    
3      4         A    20    24    310          0.23506   0.42239    31        31        2.00000
3      5         A    24    28    551          0.38105   0.16617    19        19        0.0    
3      6         A    28    32    1,054        0.57424   0.36797    34        34        0.0    
3      7         A    32    36    429          0.28114   0.22810    33        33        1.00000
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= =======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
A    18        22    
==== ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
read_source_models 0.15520 0.00293 0.15313 0.15727 2      
split_filter       0.10182 0.05671 0.02500 0.17794 5      
build_ruptures     1.03442 0.23375 0.53150 1.30184 18     
================== ======= ======= ======= ======= =======

Data transfer
-------------
================== ============================================================================== =========
task               sent                                                                           received 
read_source_models monitor=736 B converter=638 B fnames=382 B                                     20.26 KB 
split_filter       srcs=158.07 KB monitor=1.86 KB srcfilter=1.07 KB sample_factor=105 B seed=70 B 424.1 KB 
build_ruptures     srcs=435.57 KB param=8.19 KB monitor=6.47 KB srcfilter=3.87 KB                 569.85 KB
================== ============================================================================== =========

Slowest operations
------------------
======================== ========= ========= ======
operation                time_sec  memory_mb counts
======================== ========= ========= ======
total build_ruptures     18        0.59766   18    
saving ruptures          1.32049   0.0       1     
total split_filter       0.50910   0.0       5     
total read_source_models 0.31040   0.10156   2     
updating source_info     0.20162   0.0       1     
making contexts          0.01135   0.0       15    
store source_info        0.00627   0.0       1     
setting event years      0.00112   0.0       1     
reading exposure         4.630E-04 0.0       1     
======================== ========= ========= ======