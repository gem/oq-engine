Event Based from NonParametric source
=====================================

============== ===================
checksum32     4,272,018,576      
date           2018-09-05T10:03:58
engine_version 3.2.0-gitb4ef3a4b6c
============== ===================

num_sites = 3, num_levels = 7

Parameters
----------
=============================== ==================
calculation_mode                'event_based'     
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 500.0}
investigation_time              50.0              
ses_per_logic_tree_path         2                 
truncation_level                3.0               
rupture_mesh_spacing            5.0               
complex_fault_mesh_spacing      5.0               
width_of_mfd_bin                0.3               
area_source_discretization      20.0              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     23                
master_seed                     0                 
ses_seed                        42                
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
source_model.xml 0      Active Shallow Crust 3            4           
================ ====== ==================== ============ ============

Slowest sources
---------------
========= ========================== ============ ========= ========== ========= ========= ======
source_id source_class               num_ruptures calc_time split_time num_sites num_split events
========= ========================== ============ ========= ========== ========= ========= ======
1         NonParametricSeismicSource 4            0.02139   1.383E-05  3.00000   3         4     
========= ========================== ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
========================== ========= ======
source_class               calc_time counts
========================== ========= ======
NonParametricSeismicSource 0.02139   1     
========================== ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
==================== ======= ======= ======= ======= =========
operation-duration   mean    stddev  min     max     num_tasks
pickle_source_models 0.05129 NaN     0.05129 0.05129 1        
preprocess           0.00999 0.00617 0.00198 0.01507 4        
compute_gmfs         0.00211 NaN     0.00211 0.00211 1        
==================== ======= ======= ======= ======= =========

Data transfer
-------------
==================== ============================================================================================ ========
task                 sent                                                                                         received
pickle_source_models monitor=0 B fnames=0 B converter=0 B                                                         157 B   
preprocess           srcs=17.07 KB monitor=1.25 KB param=1.14 KB srcfilter=1012 B                                 29.65 KB
compute_gmfs         sources_or_ruptures=28.54 KB param=2.26 KB monitor=307 B rlzs_by_gsim=297 B src_filter=220 B 27.4 KB 
==================== ============================================================================================ ========

Slowest operations
------------------
========================== ========= ========= ======
operation                  time_sec  memory_mb counts
========================== ========= ========= ======
total pickle_source_models 0.05129   0.0       1     
total preprocess           0.03994   0.43359   4     
making contexts            0.02007   0.0       3     
saving ruptures            0.00842   0.0       3     
store source_info          0.00370   0.0       1     
managing sources           0.00285   0.0       1     
total compute_gmfs         0.00211   0.0       1     
building ruptures          0.00144   0.0       1     
GmfGetter.init             3.047E-04 0.0       1     
splitting sources          2.387E-04 0.0       1     
aggregating hcurves        1.531E-04 0.0       1     
========================== ========= ========= ======