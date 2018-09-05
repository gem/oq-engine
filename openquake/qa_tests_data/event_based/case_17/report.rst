Event Based Hazard QA Test, Case 17
===================================

============== ===================
checksum32     2,756,942,605      
date           2018-09-05T10:04:00
engine_version 3.2.0-gitb4ef3a4b6c
============== ===================

num_sites = 1, num_levels = 3

Parameters
----------
=============================== ==================
calculation_mode                'event_based'     
number_of_logic_tree_samples    5                 
maximum_distance                {'default': 200.0}
investigation_time              1.0               
ses_per_logic_tree_path         3                 
truncation_level                2.0               
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                1.0               
area_source_discretization      20.0              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     106               
master_seed                     0                 
ses_seed                        106               
=============================== ==================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gsim_logic_tree.xml <gsim_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
source                  `source_model_1.xml <source_model_1.xml>`_                  
source                  `source_model_2.xml <source_model_2.xml>`_                  
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
b1        0.20000 trivial(1)      3/1             
b2        0.20000 trivial(1)      2/1             
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================ ========= ========== ==========
grp_id gsims            distances siteparams ruptparams
====== ================ ========= ========== ==========
0      SadighEtAl1997() rrup      vs30       mag rake  
1      SadighEtAl1997() rrup      vs30       mag rake  
====== ================ ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=2, rlzs=5)
  0,SadighEtAl1997(): [0 1 2]
  1,SadighEtAl1997(): [3 4]>

Number of ruptures per tectonic region type
-------------------------------------------
================== ====== ==================== ============ ============
source_model       grp_id trt                  eff_ruptures tot_ruptures
================== ====== ==================== ============ ============
source_model_1.xml 0      Active Shallow Crust 39           39          
source_model_2.xml 1      Active Shallow Crust 7            7           
================== ====== ==================== ============ ============

============= ==
#TRT models   2 
#eff_ruptures 46
#tot_ruptures 46
#tot_weight   0 
============= ==

Slowest sources
---------------
========= ============ ============ ========= ========== ========= ========= ======
source_id source_class num_ruptures calc_time split_time num_sites num_split events
========= ============ ============ ========= ========== ========= ========= ======
1         PointSource  39           0.02122   3.576E-06  1.00000   1         0     
2         PointSource  7            0.00906   1.192E-06  1.00000   1         13    
========= ============ ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
PointSource  0.03028   2     
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
==================== ======= ========= ======= ======= =========
operation-duration   mean    stddev    min     max     num_tasks
pickle_source_models 0.00179 9.852E-04 0.00109 0.00248 2        
preprocess           0.01936 0.00812   0.01361 0.02510 2        
compute_gmfs         0.01114 NaN       0.01114 0.01114 1        
==================== ======= ========= ======= ======= =========

Data transfer
-------------
==================== =========================================================================================== ========
task                 sent                                                                                        received
pickle_source_models monitor=618 B converter=578 B fnames=372 B                                                  324 B   
preprocess           srcs=3.03 KB monitor=638 B param=570 B srcfilter=506 B                                      6.72 KB 
compute_gmfs         sources_or_ruptures=4.94 KB param=2.28 KB monitor=307 B rlzs_by_gsim=292 B src_filter=220 B 4.75 KB 
==================== =========================================================================================== ========

Slowest operations
------------------
========================== ========= ========= ======
operation                  time_sec  memory_mb counts
========================== ========= ========= ======
total preprocess           0.03871   0.0       2     
total compute_gmfs         0.01114   0.0       1     
building hazard            0.00676   0.0       1     
store source_info          0.00568   0.0       1     
saving ruptures            0.00539   0.0       1     
total pickle_source_models 0.00357   0.12109   2     
managing sources           0.00306   0.0       1     
building ruptures          0.00253   0.0       1     
saving gmfs                0.00204   0.0       1     
making contexts            0.00158   0.0       3     
saving gmf_data/indices    0.00126   0.0       1     
GmfGetter.init             5.376E-04 0.0       1     
building hazard curves     4.766E-04 0.0       2     
splitting sources          2.925E-04 0.0       1     
aggregating hcurves        2.792E-04 0.0       1     
========================== ========= ========= ======