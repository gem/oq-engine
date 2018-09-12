Event Based QA Test, Case 3
===========================

============== ===================
checksum32     2,879,210,841      
date           2018-09-05T10:04:08
engine_version 3.2.0-gitb4ef3a4b6c
============== ===================

num_sites = 1, num_levels = 3

Parameters
----------
=============================== ==================
calculation_mode                'event_based'     
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              2.0               
ses_per_logic_tree_path         2                 
truncation_level                2.0               
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                1.0               
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
b1        1.00000 simple(2)       2/2             
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================================== ========= ========== ==========
grp_id gsims                              distances siteparams ruptparams
====== ================================== ========= ========== ==========
0      AkkarBommer2010() SadighEtAl1997() rjb rrup  vs30       mag rake  
====== ================================== ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=2, rlzs=2)
  0,AkkarBommer2010(): [1]
  0,SadighEtAl1997(): [0]>

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
1         PointSource  1            0.00105   2.861E-06  1.00000   1         7     
========= ============ ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
PointSource  0.00105   1     
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
==================== ========= ====== ========= ========= =========
operation-duration   mean      stddev min       max       num_tasks
pickle_source_models 9.236E-04 NaN    9.236E-04 9.236E-04 1        
preprocess           0.00291   NaN    0.00291   0.00291   1        
compute_gmfs         0.00440   NaN    0.00440   0.00440   1        
==================== ========= ====== ========= ========= =========

Data transfer
-------------
==================== =========================================================================================== ========
task                 sent                                                                                        received
pickle_source_models monitor=0 B fnames=0 B converter=0 B                                                        157 B   
preprocess           srcs=0 B srcfilter=0 B param=0 B monitor=0 B                                                3.05 KB 
compute_gmfs         sources_or_ruptures=3.08 KB param=2.28 KB rlzs_by_gsim=411 B monitor=307 B src_filter=220 B 2.13 KB 
==================== =========================================================================================== ========

Slowest operations
------------------
========================== ========= ========= ======
operation                  time_sec  memory_mb counts
========================== ========= ========= ======
total compute_gmfs         0.00440   0.0       1     
store source_info          0.00388   0.0       1     
building ruptures          0.00305   0.0       1     
total preprocess           0.00291   0.0       1     
saving ruptures            0.00272   0.0       1     
managing sources           0.00239   0.0       1     
total pickle_source_models 9.236E-04 0.0       1     
GmfGetter.init             5.357E-04 0.0       1     
making contexts            5.178E-04 0.0       1     
splitting sources          2.420E-04 0.0       1     
aggregating hcurves        1.829E-04 0.0       1     
========================== ========= ========= ======