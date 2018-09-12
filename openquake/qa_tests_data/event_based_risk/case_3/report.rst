Event Based Risk Lisbon
=======================

============== ===================
checksum32     3,187,009,563      
date           2018-09-05T10:04:27
engine_version 3.2.0-gitb4ef3a4b6c
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
0         AreaSource   6,075        7.77293   0.03563    1.00000   270       3     
2         AreaSource   4,901        5.04155   0.03750    1.00000   228       2     
6         AreaSource   1,054        1.66050   0.01039    1.00000   68        0     
10        AreaSource   1,116        1.46914   0.01833    1.00000   124       0     
1         AreaSource   989          1.38556   0.00862    1.00000   86        4     
3         AreaSource   812          0.95298   0.00617    1.00000   56        0     
5         AreaSource   551          0.89295   0.00877    1.00000   38        1     
9         AreaSource   612          0.85858   0.01237    1.00000   98        0     
8         AreaSource   342          0.52416   0.00549    1.00000   38        0     
7         AreaSource   429          0.36218   0.00695    1.00000   66        1     
4         AreaSource   310          0.35079   0.01313    1.00000   62        2     
========= ============ ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
AreaSource   21        11    
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
==================== ======= ======= ======= ======= =========
operation-duration   mean    stddev  min     max     num_tasks
pickle_source_models 0.18841 0.00387 0.18568 0.19115 2        
preprocess           1.23482 0.35495 0.58263 1.63217 18       
compute_gmfs         0.00537 0.00255 0.00288 0.00768 4        
==================== ======= ======= ======= ======= =========

Data transfer
-------------
==================== ================================================================================================= =========
task                 sent                                                                                              received 
pickle_source_models monitor=692 B converter=578 B fnames=382 B                                                        336 B    
preprocess           srcs=427.68 KB param=8.14 KB monitor=6.28 KB srcfilter=4.45 KB                                    516.97 KB
compute_gmfs         sources_or_ruptures=26.61 KB param=16.57 KB rlzs_by_gsim=1.66 KB monitor=1.35 KB src_filter=880 B 17.86 KB 
==================== ================================================================================================= =========

Slowest operations
------------------
========================== ========= ========= ======
operation                  time_sec  memory_mb counts
========================== ========= ========= ======
total preprocess           22        7.91797   18    
total pickle_source_models 0.37683   4.76172   2     
splitting sources          0.32552   0.0       1     
saving ruptures            0.03459   0.0       13    
total compute_gmfs         0.02148   4.59375   4     
building ruptures          0.01497   4.42969   4     
making contexts            0.01304   0.0       15    
managing sources           0.00501   0.0       1     
store source_info          0.00472   0.0       1     
GmfGetter.init             0.00325   0.06250   4     
setting event years        0.00130   0.0       1     
reading exposure           9.277E-04 0.0       1     
aggregating hcurves        8.509E-04 0.0       4     
========================== ========= ========= ======