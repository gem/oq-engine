Event Based Risk Lisbon
=======================

============== ===================
checksum32     2,968,384,188      
date           2018-05-15T04:12:52
engine_version 3.1.0-git0acbc11   
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
#tot_weight   3,438 
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
0         PointSource  45           8.36316   0.0        270       270       56    
2         PointSource  29           4.84852   0.0        228       228       140   
6         PointSource  31           1.60734   0.0        68        68        34    
1         PointSource  23           1.40428   0.0        86        86        42    
10        PointSource  18           1.27615   0.0        124       124       0     
3         PointSource  29           1.13471   0.0        56        56        0     
5         PointSource  29           0.89765   0.0        38        38        12    
9         PointSource  12           0.77147   0.0        98        98        0     
8         PointSource  18           0.54053   0.0        38        38        2     
4         PointSource  10           0.50887   0.0        62        62        9     
7         PointSource  13           0.37450   0.0        66        66        41    
========= ============ ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
PointSource  21        11    
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =========
operation-duration mean    stddev  min     max     num_tasks
prefilter          0.01071 0.00691 0.00332 0.03371 60       
compute_ruptures   1.22239 0.36862 0.51383 1.67929 18       
================== ======= ======= ======= ======= =========

Informational data
------------------
================ ================================================================================ =========
task             sent                                                                             received 
prefilter        srcs=463.61 KB monitor=18.93 KB srcfilter=13.42 KB                               475.29 KB
compute_ruptures sources=422.89 KB param=15.52 KB src_filter=12.6 KB monitor=5.8 KB gsims=3.87 KB 82.95 KB 
================ ================================================================================ =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total compute_ruptures         22        1.08594   18    
managing sources               1.99205   0.0       1     
total prefilter                0.64236   3.43359   60    
reading composite source model 0.40485   0.0       1     
splitting sources              0.36003   0.0       1     
saving ruptures                0.02392   0.0       18    
unpickling prefilter           0.02181   0.0       60    
making contexts                0.01407   0.0       15    
store source_info              0.00966   0.0       1     
unpickling compute_ruptures    0.00462   0.0       18    
reading site collection        0.00245   0.0       1     
setting event years            0.00244   0.0       1     
reading exposure               9.508E-04 0.0       1     
============================== ========= ========= ======