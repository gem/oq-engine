QA test for blocksize independence (hazard)
===========================================

============== ===================
checksum32     2,348,158,649      
date           2018-09-05T10:03:50
engine_version 3.2.0-gitb4ef3a4b6c
============== ===================

num_sites = 2, num_levels = 4

Parameters
----------
=============================== ==================
calculation_mode                'event_based'     
number_of_logic_tree_samples    1                 
maximum_distance                {'default': 400.0}
investigation_time              5.0               
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            20.0              
complex_fault_mesh_spacing      20.0              
width_of_mfd_bin                0.5               
area_source_discretization      20.0              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     42                
master_seed                     0                 
ses_seed                        1024              
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
source_model.xml 0      Active Shallow Crust 2,625        5,572       
================ ====== ==================== ============ ============

Slowest sources
---------------
========= ============ ============ ========= ========== ========= ========= ======
source_id source_class num_ruptures calc_time split_time num_sites num_split events
========= ============ ============ ========= ========== ========= ========= ======
1         AreaSource   1,752        1.66662   0.08454    2.00000   292       1     
2         AreaSource   582          0.49096   0.02684    2.00000   97        3     
3         AreaSource   440          0.20943   0.02230    2.00000   57        0     
9         AreaSource   222          0.00348   0.02861    1.50000   2         0     
4         AreaSource   267          0.0       0.02762    0.0       0         0     
5         AreaSource   518          0.0       0.08698    0.0       0         0     
6         AreaSource   316          0.0       0.04594    0.0       0         0     
7         AreaSource   1,028        0.0       0.08723    0.0       0         0     
8         AreaSource   447          0.0       0.08328    0.0       0         0     
========= ============ ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
AreaSource   2.37049   9     
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
==================== ======= ======= ======= ======= =========
operation-duration   mean    stddev  min     max     num_tasks
pickle_source_models 0.48267 NaN     0.48267 0.48267 1        
preprocess           0.05110 0.04953 0.00117 0.15580 62       
compute_gmfs         0.00222 NaN     0.00222 0.00222 1        
==================== ======= ======= ======= ======= =========

Data transfer
-------------
==================== =========================================================================================== =========
task                 sent                                                                                        received 
pickle_source_models monitor=0 B fnames=0 B converter=0 B                                                        160 B    
preprocess           srcs=402.17 KB monitor=19.31 KB param=17.68 KB srcfilter=15.32 KB                           192.13 KB
compute_gmfs         sources_or_ruptures=9.51 KB param=2.26 KB monitor=307 B rlzs_by_gsim=297 B src_filter=220 B 6.99 KB  
==================== =========================================================================================== =========

Slowest operations
------------------
========================== ========= ========= ======
operation                  time_sec  memory_mb counts
========================== ========= ========= ======
total preprocess           3.16820   7.98438   62    
splitting sources          0.49530   0.0       1     
total pickle_source_models 0.48267   0.0       1     
saving ruptures            0.01065   0.14453   4     
making contexts            0.00689   0.0       5     
store source_info          0.00437   0.17969   1     
managing sources           0.00319   0.0       1     
total compute_gmfs         0.00222   0.0       1     
building ruptures          0.00143   0.0       1     
GmfGetter.init             3.185E-04 0.0       1     
aggregating hcurves        1.554E-04 0.0       1     
========================== ========= ========= ======