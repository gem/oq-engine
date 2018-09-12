Event-Based Hazard QA Test, Case 18
===================================

============== ===================
checksum32     98,343,102         
date           2018-09-05T10:04:13
engine_version 3.2.0-gitb4ef3a4b6c
============== ===================

num_sites = 1, num_levels = 4

Parameters
----------
=============================== ==================
calculation_mode                'event_based'     
number_of_logic_tree_samples    3                 
maximum_distance                {'default': 200.0}
investigation_time              1.0               
ses_per_logic_tree_path         350               
truncation_level                0.0               
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                0.001             
area_source_discretization      20.0              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     1064              
master_seed                     0                 
ses_seed                        1064              
=============================== ==================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `three_gsim_logic_tree.xml <three_gsim_logic_tree.xml>`_    
job_ini                 `job.ini <job.ini>`_                                        
source                  `source_model.xml <source_model.xml>`_                      
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
b1        0.33333 simple(3)       3/3             
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ======================================================== ================= ======================= =================
grp_id gsims                                                    distances         siteparams              ruptparams       
====== ======================================================== ================= ======================= =================
0      AkkarBommer2010() CauzziFaccioli2008() ChiouYoungs2008() rhypo rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
====== ======================================================== ================= ======================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=2, rlzs=3)
  0,AkkarBommer2010(): [0 2]
  0,ChiouYoungs2008(): [1]>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== ============ ============
source_model     grp_id trt                  eff_ruptures tot_ruptures
================ ====== ==================== ============ ============
source_model.xml 0      Active Shallow Crust 3,000        3,000       
================ ====== ==================== ============ ============

Slowest sources
---------------
========= ============ ============ ========= ========== ========= ========= ======
source_id source_class num_ruptures calc_time split_time num_sites num_split events
========= ============ ============ ========= ========== ========= ========= ======
1         PointSource  3,000        6.66350   2.623E-06  1.00000   1         6     
========= ============ ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
PointSource  6.66350   1     
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
==================== ======= ====== ======= ======= =========
operation-duration   mean    stddev min     max     num_tasks
pickle_source_models 0.00426 NaN    0.00426 0.00426 1        
preprocess           6.66881 NaN    6.66881 6.66881 1        
compute_gmfs         0.00483 NaN    0.00483 0.00483 1        
==================== ======= ====== ======= ======= =========

Data transfer
-------------
==================== =========================================================================================== ========
task                 sent                                                                                        received
pickle_source_models monitor=0 B fnames=0 B converter=0 B                                                        158 B   
preprocess           srcs=0 B srcfilter=0 B param=0 B monitor=0 B                                                20.4 KB 
compute_gmfs         sources_or_ruptures=20.51 KB param=2.5 KB rlzs_by_gsim=420 B monitor=307 B src_filter=220 B 7.66 KB 
==================== =========================================================================================== ========

Slowest operations
------------------
========================== ========= ========= ======
operation                  time_sec  memory_mb counts
========================== ========= ========= ======
total preprocess           6.66881   0.0       1     
total compute_gmfs         0.00483   0.0       1     
total pickle_source_models 0.00426   0.0       1     
saving ruptures            0.00410   0.0       1     
store source_info          0.00409   0.0       1     
making contexts            0.00367   0.0       6     
building ruptures          0.00315   0.0       1     
managing sources           0.00297   0.0       1     
GmfGetter.init             8.550E-04 0.0       1     
splitting sources          2.120E-04 0.0       1     
aggregating hcurves        1.812E-04 0.0       1     
========================== ========= ========= ======