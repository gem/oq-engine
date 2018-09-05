Event Based QA Test, Case 13
============================

============== ===================
checksum32     2,624,926,206      
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
investigation_time              1.0               
ses_per_logic_tree_path         5000              
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
1         PointSource  1            0.02001   3.099E-06  1.00000   1         5,031 
========= ============ ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
PointSource  0.02001   1     
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
==================== ========= ====== ========= ========= =========
operation-duration   mean      stddev min       max       num_tasks
pickle_source_models 9.444E-04 NaN    9.444E-04 9.444E-04 1        
preprocess           0.02188   NaN    0.02188   0.02188   1        
compute_gmfs         0.09162   NaN    0.09162   0.09162   1        
==================== ========= ====== ========= ========= =========

Data transfer
-------------
==================== ============================================================================================ =========
task                 sent                                                                                         received 
pickle_source_models monitor=0 B fnames=0 B converter=0 B                                                         158 B    
preprocess           srcs=0 B srcfilter=0 B param=0 B monitor=0 B                                                 130.58 KB
compute_gmfs         sources_or_ruptures=91.36 KB param=2.28 KB monitor=307 B rlzs_by_gsim=301 B src_filter=220 B 179.39 KB
==================== ============================================================================================ =========

Slowest operations
------------------
========================== ========= ========= ======
operation                  time_sec  memory_mb counts
========================== ========= ========= ======
total compute_gmfs         0.09162   0.23828   1     
building hazard            0.07996   0.23828   1     
total preprocess           0.02188   0.0       1     
saving ruptures            0.02134   0.0       1     
store source_info          0.00368   0.0       1     
building ruptures          0.00333   0.0       1     
saving gmfs                0.00311   0.0       1     
managing sources           0.00264   0.0       1     
GmfGetter.init             0.00192   0.0       1     
saving gmf_data/indices    0.00122   0.0       1     
total pickle_source_models 9.444E-04 0.0       1     
making contexts            3.848E-04 0.0       1     
aggregating hcurves        3.672E-04 0.0       1     
splitting sources          2.341E-04 0.0       1     
building hazard curves     1.352E-04 0.0       1     
========================== ========= ========= ======