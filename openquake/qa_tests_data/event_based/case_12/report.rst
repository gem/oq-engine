Event Based QA Test, Case 12
============================

============== ===================
checksum32     1,316,139,513      
date           2018-09-05T10:04:09
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
ses_per_logic_tree_path         3500              
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
b1        1.00000 trivial(1,1)    1/1             
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== =================== ========= ========== ==========
grp_id gsims               distances siteparams ruptparams
====== =================== ========= ========== ==========
0      SadighEtAl1997()    rrup      vs30       mag rake  
1      BooreAtkinson2008() rjb       vs30       mag rake  
====== =================== ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=2, rlzs=1)
  0,SadighEtAl1997(): [0]
  1,BooreAtkinson2008(): [0]>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== ============ ============
source_model     grp_id trt                  eff_ruptures tot_ruptures
================ ====== ==================== ============ ============
source_model.xml 0      Active Shallow Crust 1            1           
source_model.xml 1      Stable Continental   1            1           
================ ====== ==================== ============ ============

============= =
#TRT models   2
#eff_ruptures 2
#tot_ruptures 2
#tot_weight   0
============= =

Slowest sources
---------------
========= ============ ============ ========= ========== ========= ========= ======
source_id source_class num_ruptures calc_time split_time num_sites num_split events
========= ============ ============ ========= ========== ========= ========= ======
1         PointSource  1            0.02072   3.576E-06  1.00000   1         3,536 
2         PointSource  1            0.02023   1.431E-06  1.00000   1         3,370 
========= ============ ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
PointSource  0.04096   2     
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
==================== ======= ======= ======= ======= =========
operation-duration   mean    stddev  min     max     num_tasks
pickle_source_models 0.00135 NaN     0.00135 0.00135 1        
preprocess           0.02421 0.00127 0.02332 0.02511 2        
compute_gmfs         0.06747 0.00395 0.06468 0.07026 2        
==================== ======= ======= ======= ======= =========

Data transfer
-------------
==================== ============================================================================================= =========
task                 sent                                                                                          received 
pickle_source_models monitor=0 B fnames=0 B converter=0 B                                                          158 B    
preprocess           srcs=2.57 KB param=806 B monitor=638 B srcfilter=506 B                                        181.09 KB
compute_gmfs         sources_or_ruptures=127.31 KB param=4.76 KB monitor=614 B rlzs_by_gsim=591 B src_filter=440 B 247.8 KB 
==================== ============================================================================================= =========

Slowest operations
------------------
========================== ========= ========= ======
operation                  time_sec  memory_mb counts
========================== ========= ========= ======
total compute_gmfs         0.13495   0.25000   2     
building hazard            0.11798   0.25000   2     
total preprocess           0.04843   0.08984   2     
saving ruptures            0.03265   0.0       2     
building ruptures          0.00493   0.0       2     
store source_info          0.00386   0.0       1     
saving gmfs                0.00367   0.0       2     
managing sources           0.00293   0.0       1     
GmfGetter.init             0.00266   0.0       2     
total pickle_source_models 0.00135   0.0       1     
saving gmf_data/indices    9.365E-04 0.0       1     
making contexts            8.247E-04 0.0       2     
splitting sources          5.023E-04 0.0       1     
aggregating hcurves        3.951E-04 0.0       2     
building hazard curves     2.844E-04 0.0       2     
========================== ========= ========= ======