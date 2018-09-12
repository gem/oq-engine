Event Based Risk QA Test 2
==========================

============== ===================
checksum32     3,857,499,779      
date           2018-09-05T10:04:30
engine_version 3.2.0-gitb4ef3a4b6c
============== ===================

num_sites = 3, num_levels = 15

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
======================== ==============================================================
Name                     File                                                          
======================== ==============================================================
exposure                 `exposure.xml <exposure.xml>`_                                
gsim_logic_tree          `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                  
job_ini                  `job.ini <job.ini>`_                                          
source                   `source_model.xml <source_model.xml>`_                        
source_model_logic_tree  `source_model_logic_tree.xml <source_model_logic_tree.xml>`_  
structural_vulnerability `vulnerability_model_stco.xml <vulnerability_model_stco.xml>`_
======================== ==============================================================

Composite source model
----------------------
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
b1        1.00000 trivial(1)      1/1             
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================= =========== ======================= =================
grp_id gsims             distances   siteparams              ruptparams       
====== ================= =========== ======================= =================
0      ChiouYoungs2008() rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
====== ================= =========== ======================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)
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
4 asset(s) x 1 realization(s) x 1 loss type(s) x 2 losses x 8 bytes x 60 tasks = 3.75 KB

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
RC+      1.00000 NaN     1   1   1         1         
W/1      1.00000 NaN     1   1   1         1         
*ALL*    1.33333 0.57735 1   2   3         4         
======== ======= ======= === === ========= ==========

Slowest sources
---------------
========= ============ ============ ========= ========== ========= ========= ======
source_id source_class num_ruptures calc_time split_time num_sites num_split events
========= ============ ============ ========= ========== ========= ========= ======
1         PointSource  6            0.00700   5.960E-06  1.00000   1         8     
2         PointSource  6            0.00697   1.192E-06  1.00000   1         6     
3         PointSource  6            0.00558   7.153E-07  1.00000   1         6     
========= ============ ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
PointSource  0.01955   3     
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
==================== ======= ======= ======= ======= =========
operation-duration   mean    stddev  min     max     num_tasks
pickle_source_models 0.00207 NaN     0.00207 0.00207 1        
preprocess           0.01747 0.00162 0.01561 0.01847 3        
compute_gmfs         0.01122 NaN     0.01122 0.01122 1        
==================== ======= ======= ======= ======= =========

Data transfer
-------------
==================== ============================================================================================ ========
task                 sent                                                                                         received
pickle_source_models monitor=0 B fnames=0 B converter=0 B                                                         162 B   
preprocess           srcs=3.95 KB monitor=1.05 KB param=876 B srcfilter=759 B                                     16.23 KB
compute_gmfs         sources_or_ruptures=13.99 KB param=3.22 KB monitor=345 B rlzs_by_gsim=297 B src_filter=220 B 11.76 KB
==================== ============================================================================================ ========

Slowest operations
------------------
========================== ========= ========= ======
operation                  time_sec  memory_mb counts
========================== ========= ========= ======
total preprocess           0.05242   8.07422   3     
total compute_gmfs         0.01122   5.56250   1     
saving ruptures            0.00992   0.0       3     
building ruptures          0.00730   5.39453   1     
making contexts            0.00636   0.0       9     
store source_info          0.00377   0.0       1     
managing sources           0.00350   0.0       1     
GmfGetter.init             0.00252   0.0       1     
total pickle_source_models 0.00222   0.00391   3     
setting event years        0.00170   0.0       1     
reading exposure           0.00148   0.0       1     
aggregating hcurves        2.534E-04 0.0       1     
splitting sources          2.449E-04 0.0       1     
========================== ========= ========= ======