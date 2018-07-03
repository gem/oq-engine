Event Based Risk QA Test 1
==========================

============== ===================
checksum32     348,816,558        
date           2018-06-05T06:38:42
engine_version 3.2.0-git65c4735   
============== ===================

num_sites = 3, num_levels = 25

Parameters
----------
=============================== ==================
calculation_mode                'event_based_risk'
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 100.0}
investigation_time              50.0              
ses_per_logic_tree_path         20                
truncation_level                3.0               
rupture_mesh_spacing            5.0               
complex_fault_mesh_spacing      5.0               
width_of_mfd_bin                0.3               
area_source_discretization      10.0              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     23                
master_seed                     42                
ses_seed                        42                
avg_losses                      True              
=============================== ==================

Input files
-----------
=========================== ====================================================================
Name                        File                                                                
=========================== ====================================================================
exposure                    `exposure.xml <exposure.xml>`_                                      
gsim_logic_tree             `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                        
job_ini                     `job.ini <job.ini>`_                                                
nonstructural_vulnerability `vulnerability_model_nonstco.xml <vulnerability_model_nonstco.xml>`_
source                      `source_model.xml <source_model.xml>`_                              
source_model_logic_tree     `source_model_logic_tree.xml <source_model_logic_tree.xml>`_        
structural_vulnerability    `vulnerability_model_stco.xml <vulnerability_model_stco.xml>`_      
=========================== ====================================================================

Composite source model
----------------------
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
b1        1.00000 simple(2)       2/2             
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== =================================== =========== ======================= =================
grp_id gsims                               distances   siteparams              ruptparams       
====== =================================== =========== ======================= =================
0      AkkarBommer2010() ChiouYoungs2008() rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
====== =================================== =========== ======================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=2, rlzs=2)
  0,AkkarBommer2010(): [1]
  0,ChiouYoungs2008(): [0]>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== ============ ============
source_model     grp_id trt                  eff_ruptures tot_ruptures
================ ====== ==================== ============ ============
source_model.xml 0      Active Shallow Crust 18           18          
================ ====== ==================== ============ ============

Estimated data transfer for the avglosses
-----------------------------------------
4 asset(s) x 2 realization(s) x 2 loss type(s) x 1 losses x 8 bytes x 60 tasks = 7.5 KB

Exposure model
--------------
=============== ========
#assets         4       
#taxonomies     3       
deductibile     absolute
insurance_limit absolute
=============== ========

======== ======= ======= === === ========= ==========
taxonomy mean    stddev  min max num_sites num_assets
RM       1.00000 0.0     1   1   2         2         
RC       1.00000 NaN     1   1   1         1         
W        1.00000 NaN     1   1   1         1         
*ALL*    1.33333 0.57735 1   2   3         4         
======== ======= ======= === === ========= ==========

Slowest sources
---------------
========= ============ ============ ========= ========== ========= ========= ======
source_id source_class num_ruptures calc_time split_time num_sites num_split events
========= ============ ============ ========= ========== ========= ========= ======
1         PointSource  6            0.01003   3.815E-06  1.00000   1         8     
2         PointSource  6            0.00744   1.669E-06  1.00000   1         14    
3         PointSource  6            0.00724   1.192E-06  1.00000   1         20    
========= ============ ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
PointSource  0.02471   3     
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ========= ======= ======= =========
operation-duration mean    stddev    min     max     num_tasks
RtreeFilter        0.00270 1.784E-04 0.00258 0.00290 3        
compute_ruptures   0.03375 NaN       0.03375 0.03375 1        
================== ======= ========= ======= ======= =========

Data transfer
-------------
================ ======================================================================== ========
task             sent                                                                     received
RtreeFilter      srcs=3.91 KB monitor=1.01 KB srcfilter=837 B                             4.05 KB 
compute_ruptures sources=2.47 KB param=1.03 KB monitor=353 B src_filter=233 B gsims=216 B 11.3 KB 
================ ======================================================================== ========

Slowest operations
------------------
=============================== ========= ========= ======
operation                       time_sec  memory_mb counts
=============================== ========= ========= ======
EventBasedRuptureCalculator.run 0.35852   0.0       1     
managing sources                0.19791   0.0       1     
total compute_ruptures          0.03375   7.37500   1     
making contexts                 0.00959   0.0       9     
total prefilter                 0.00810   2.47656   3     
store source_info               0.00582   0.0       1     
saving ruptures                 0.00556   0.0       1     
reading composite source model  0.00347   0.0       1     
reading site collection         0.00278   0.0       1     
setting event years             0.00164   0.0       1     
reading exposure                0.00142   0.0       1     
unpickling compute_ruptures     0.00127   0.0       1     
unpickling prefilter            8.237E-04 0.0       3     
splitting sources               3.107E-04 0.0       1     
=============================== ========= ========= ======