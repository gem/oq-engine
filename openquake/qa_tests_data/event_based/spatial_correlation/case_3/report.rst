Probabilistic Event-Based QA Test with No Spatial Correlation, case 3
=====================================================================

============== ===================
checksum32     3,678,589,439      
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
ses_per_logic_tree_path         300               
truncation_level                None              
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                0.1               
area_source_discretization      20.0              
ground_motion_correlation_model None              
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
1         PointSource  1            0.02450   2.861E-06  2.00000   1         45,319
========= ============ ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
PointSource  0.02450   1     
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
==================== ========= ====== ========= ========= =========
operation-duration   mean      stddev min       max       num_tasks
pickle_source_models 8.948E-04 NaN    8.948E-04 8.948E-04 1        
preprocess           0.02655   NaN    0.02655   0.02655   1        
compute_gmfs         0.17952   NaN    0.17952   0.17952   1        
==================== ========= ====== ========= ========= =========

Data transfer
-------------
==================== ============================================================================================= ========
task                 sent                                                                                          received
pickle_source_models monitor=0 B fnames=0 B converter=0 B                                                          177 B   
preprocess           srcs=0 B srcfilter=0 B param=0 B monitor=0 B                                                  1.13 MB 
compute_gmfs         sources_or_ruptures=799.57 KB param=2.26 KB monitor=307 B rlzs_by_gsim=301 B src_filter=220 B 1.12 MB 
==================== ============================================================================================= ========

Slowest operations
------------------
========================== ========= ========= ======
operation                  time_sec  memory_mb counts
========================== ========= ========= ======
total compute_gmfs         0.17952   6.33203   1     
saving ruptures            0.16270   0.0       1     
total preprocess           0.02655   0.0       1     
GmfGetter.init             0.00724   5.76953   1     
store source_info          0.00393   0.0       1     
building ruptures          0.00342   0.00391   1     
managing sources           0.00279   0.0       1     
total pickle_source_models 8.948E-04 0.0       1     
aggregating hcurves        5.550E-04 0.0       1     
making contexts            3.846E-04 0.0       1     
splitting sources          2.382E-04 0.0       1     
========================== ========= ========= ======