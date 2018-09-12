Event-Based Hazard QA Test, Case 2
==================================

============== ===================
checksum32     2,757,562,625      
date           2018-09-05T10:04:09
engine_version 3.2.0-gitb4ef3a4b6c
============== ===================

num_sites = 1, num_levels = 4

Parameters
----------
=============================== ==================
calculation_mode                'event_based'     
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              1.0               
ses_per_logic_tree_path         600               
truncation_level                0.0               
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                0.001             
area_source_discretization      20.0              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     42                
master_seed                     0                 
ses_seed                        1066              
=============================== ==================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gsim_logic_tree.xml <gsim_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
source                  `source_model.xml <source_model.xml>`_                      
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
b1        1.00000 trivial(1)      1/1             
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================ ========= ========== ==========
grp_id gsims            distances siteparams ruptparams
====== ================ ========= ========== ==========
0      SadighEtAl1997() rrup      vs30       mag rake  
====== ================ ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)
  0,SadighEtAl1997(): [0]>

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
1         PointSource  3,000        4.45259   2.623E-06  1.00000   1         3     
========= ============ ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
PointSource  4.45259   1     
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
==================== ======= ====== ======= ======= =========
operation-duration   mean    stddev min     max     num_tasks
pickle_source_models 0.00456 NaN    0.00456 0.00456 1        
preprocess           4.45788 NaN    4.45788 4.45788 1        
compute_gmfs         0.00592 NaN    0.00592 0.00592 1        
==================== ======= ====== ======= ======= =========

Data transfer
-------------
==================== ============================================================================================ ========
task                 sent                                                                                         received
pickle_source_models monitor=0 B fnames=0 B converter=0 B                                                         157 B   
preprocess           srcs=0 B srcfilter=0 B param=0 B monitor=0 B                                                 16.29 KB
compute_gmfs         sources_or_ruptures=16.36 KB param=2.28 KB monitor=307 B rlzs_by_gsim=290 B src_filter=220 B 4.27 KB 
==================== ============================================================================================ ========

Slowest operations
------------------
========================== ========= ========= ======
operation                  time_sec  memory_mb counts
========================== ========= ========= ======
total preprocess           4.45788   0.0       1     
total compute_gmfs         0.00592   0.0       1     
total pickle_source_models 0.00456   0.0       1     
store source_info          0.00361   0.0       1     
saving ruptures            0.00346   0.0       1     
building ruptures          0.00315   0.0       1     
managing sources           0.00278   0.0       1     
saving gmfs                0.00219   0.0       1     
building hazard            0.00119   0.0       1     
saving gmf_data/indices    0.00101   0.0       1     
making contexts            6.497E-04 0.0       3     
GmfGetter.init             5.491E-04 0.0       1     
splitting sources          4.210E-04 0.0       1     
aggregating hcurves        4.039E-04 0.0       1     
building hazard curves     1.545E-04 0.0       1     
========================== ========= ========= ======