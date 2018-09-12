Event Based Risk SJ
===================

============== ===================
checksum32     2,235,537,411      
date           2018-09-05T10:04:00
engine_version 3.2.0-gitb4ef3a4b6c
============== ===================

num_sites = 61, num_levels = 1

Parameters
----------
=============================== =================
calculation_mode                'event_based'    
number_of_logic_tree_samples    0                
maximum_distance                {'default': 50.0}
investigation_time              25.0             
ses_per_logic_tree_path         1                
truncation_level                3.0              
rupture_mesh_spacing            5.0              
complex_fault_mesh_spacing      5.0              
width_of_mfd_bin                0.3              
area_source_discretization      20.0             
ground_motion_correlation_model 'JB2009'         
minimum_intensity               {}               
random_seed                     23               
master_seed                     0                
ses_seed                        42               
=============================== =================

Input files
-----------
======================= ====================================================================
Name                    File                                                                
======================= ====================================================================
gsim_logic_tree         `Costa_Rica_RESIS_II_gmpe_CQ.xml <Costa_Rica_RESIS_II_gmpe_CQ.xml>`_
job_ini                 `job.ini <job.ini>`_                                                
site_model              `site_model_CR_60.xml <site_model_CR_60.xml>`_                      
source                  `areasource.xml <areasource.xml>`_                                  
source_model_logic_tree `sm_lt.xml <sm_lt.xml>`_                                            
======================= ====================================================================

Composite source model
----------------------
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
b1        1.00000 trivial(1,0,0)  1/1             
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================= ========= ========== ===================
grp_id gsims             distances siteparams ruptparams         
====== ================= ========= ========== ===================
0      ZhaoEtAl2006Asc() rrup      vs30       hypo_depth mag rake
====== ================= ========= ========== ===================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)
  0,ZhaoEtAl2006Asc(): [0]>

Number of ruptures per tectonic region type
-------------------------------------------
============== ====== ==================== ============ ============
source_model   grp_id trt                  eff_ruptures tot_ruptures
============== ====== ==================== ============ ============
areasource.xml 0      Active Shallow Crust 120          120         
============== ====== ==================== ============ ============

Slowest sources
---------------
========= ============ ============ ========= ========== ========= ========= ======
source_id source_class num_ruptures calc_time split_time num_sites num_split events
========= ============ ============ ========= ========== ========= ========= ======
1         AreaSource   120          0.15655   0.00478    19        20        3     
========= ============ ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
AreaSource   0.15655   1     
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
==================== ======= ======= ======= ======= =========
operation-duration   mean    stddev  min     max     num_tasks
pickle_source_models 0.00622 NaN     0.00622 0.00622 1        
preprocess           0.01412 0.00217 0.00866 0.01615 20       
compute_gmfs         0.00224 NaN     0.00224 0.00224 1        
==================== ======= ======= ======= ======= =========

Data transfer
-------------
==================== ========================================================================================== ========
task                 sent                                                                                       received
pickle_source_models monitor=0 B fnames=0 B converter=0 B                                                       153 B   
preprocess           srcs=27.45 KB param=8.44 KB monitor=6.23 KB srcfilter=4.94 KB                              35.73 KB
compute_gmfs         sources_or_ruptures=7.15 KB param=2.2 KB monitor=307 B rlzs_by_gsim=289 B src_filter=220 B 4.96 KB 
==================== ========================================================================================== ========

Slowest operations
------------------
========================== ========= ========= ======
operation                  time_sec  memory_mb counts
========================== ========= ========= ======
total preprocess           0.28248   0.26953   20    
saving ruptures            0.00832   0.0       3     
total pickle_source_models 0.00622   0.0       1     
splitting sources          0.00508   0.0       1     
store source_info          0.00452   0.0       1     
managing sources           0.00298   0.0       1     
total compute_gmfs         0.00224   0.0       1     
making contexts            0.00185   0.0       3     
building ruptures          0.00150   0.0       1     
aggregating hcurves        3.629E-04 0.0       1     
GmfGetter.init             3.557E-04 0.0       1     
========================== ========= ========= ======