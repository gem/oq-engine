Probabilistic Event-Based QA Test with Spatial Correlation, case 2
==================================================================

============== ===================
checksum32     4,018,861,831      
date           2018-09-05T10:03:59
engine_version 3.2.0-gitb4ef3a4b6c
============== ===================

num_sites = 2, num_levels = 1

Parameters
----------
=============================== ==================
calculation_mode                'event_based'     
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              50.0              
ses_per_logic_tree_path         150               
truncation_level                None              
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                0.1               
area_source_discretization      20.0              
ground_motion_correlation_model 'JB2009'          
minimum_intensity               {}                
random_seed                     42                
master_seed                     0                 
ses_seed                        123456789         
=============================== ==================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
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
====== =================== ========= ========== ==========
grp_id gsims               distances siteparams ruptparams
====== =================== ========= ========== ==========
0      BooreAtkinson2008() rjb       vs30       mag rake  
====== =================== ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)
  0,BooreAtkinson2008(): [0]>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== ============ ============
source_model     grp_id trt                  eff_ruptures tot_ruptures
================ ====== ==================== ============ ============
source_model.xml 0      Active Shallow Crust 1            1           
================ ====== ==================== ============ ============

Slowest sources
---------------
========= ============ ============ ========= ========== ========= ========= ======
source_id source_class num_ruptures calc_time split_time num_sites num_split events
========= ============ ============ ========= ========== ========= ========= ======
1         PointSource  1            0.01360   2.623E-06  2.00000   1         22,566
========= ============ ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
PointSource  0.01360   1     
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
==================== ========= ====== ========= ========= =========
operation-duration   mean      stddev min       max       num_tasks
pickle_source_models 8.399E-04 NaN    8.399E-04 8.399E-04 1        
preprocess           0.01555   NaN    0.01555   0.01555   1        
compute_gmfs         0.11425   NaN    0.11425   0.11425   1        
==================== ========= ====== ========= ========= =========

Data transfer
-------------
==================== ============================================================================================= =========
task                 sent                                                                                          received 
pickle_source_models monitor=0 B fnames=0 B converter=0 B                                                          177 B    
preprocess           srcs=0 B srcfilter=0 B param=0 B monitor=0 B                                                  575.83 KB
compute_gmfs         sources_or_ruptures=399.61 KB param=2.36 KB monitor=307 B rlzs_by_gsim=301 B src_filter=220 B 573.39 KB
==================== ============================================================================================= =========

Slowest operations
------------------
========================== ========= ========= ======
operation                  time_sec  memory_mb counts
========================== ========= ========= ======
total compute_gmfs         0.11425   2.46094   1     
saving ruptures            0.08192   0.0       1     
total preprocess           0.01555   0.0       1     
GmfGetter.init             0.00430   1.63281   1     
store source_info          0.00389   0.0       1     
building ruptures          0.00359   0.41016   1     
managing sources           0.00289   0.0       1     
total pickle_source_models 8.399E-04 0.0       1     
making contexts            3.600E-04 0.0       1     
aggregating hcurves        2.596E-04 0.0       1     
splitting sources          2.248E-04 0.0       1     
========================== ========= ========= ======