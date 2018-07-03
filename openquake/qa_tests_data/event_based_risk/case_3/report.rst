Event Based Risk Lisbon
=======================

============== ===================
checksum32     2,968,384,188      
date           2018-06-05T06:38:31
engine_version 3.2.0-git65c4735   
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
========= ============ ============ ========= ========== ========= ========= ======
source_id source_class num_ruptures calc_time split_time num_sites num_split events
========= ============ ============ ========= ========== ========= ========= ======
0         AreaSource   6,075        9.14229   0.04723    1.00000   270       63    
2         AreaSource   4,901        4.93022   0.04278    1.00000   228       162   
10        AreaSource   1,116        1.80049   0.02252    1.00000   124       0     
1         AreaSource   989          1.58030   0.01110    1.00000   86        66    
6         AreaSource   1,054        1.33715   0.01307    1.00000   68        102   
9         AreaSource   612          0.93096   0.01560    1.00000   98        49    
3         AreaSource   812          0.88397   0.00764    1.00000   56        0     
5         AreaSource   551          0.80051   0.01104    1.00000   38        41    
7         AreaSource   429          0.65461   0.00872    1.00000   66        27    
8         AreaSource   342          0.59101   0.00723    1.00000   38        19    
4         AreaSource   310          0.55689   0.01702    1.00000   62        42    
========= ============ ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
AreaSource   23        11    
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =========
operation-duration mean    stddev  min     max     num_tasks
RtreeFilter        0.01083 0.00484 0.00364 0.02409 60       
compute_ruptures   1.30234 0.29166 0.58776 1.58284 18       
================== ======= ======= ======= ======= =========

Data transfer
-------------
================ ================================================================================ =========
task             sent                                                                             received 
RtreeFilter      srcs=463.61 KB monitor=20.27 KB srcfilter=16.35 KB                               475.29 KB
compute_ruptures sources=465.75 KB param=15.86 KB monitor=6.21 KB src_filter=4.1 KB gsims=3.87 KB 80.64 KB 
================ ================================================================================ =========

Slowest operations
------------------
=============================== ======== ========= ======
operation                       time_sec memory_mb counts
=============================== ======== ========= ======
total compute_ruptures          23       7.23438   18    
EventBasedRuptureCalculator.run 3.12104  2.61719   1     
managing sources                2.08111  2.22266   1     
total prefilter                 0.64959  3.46875   60    
reading composite source model  0.40735  0.0       1     
splitting sources               0.40727  0.05469   1     
unpickling prefilter            0.04170  0.15625   60    
saving ruptures                 0.02465  0.94922   18    
making contexts                 0.01724  0.0       15    
unpickling compute_ruptures     0.00729  0.0       18    
store source_info               0.00545  0.33984   1     
reading site collection         0.00274  0.0       1     
reading exposure                0.00164  0.0       1     
setting event years             0.00125  0.0       1     
=============================== ======== ========= ======