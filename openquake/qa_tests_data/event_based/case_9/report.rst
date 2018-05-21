Event Based Risk SJ
===================

============== ===================
checksum32     1,454,548,513      
date           2018-05-15T04:14:06
engine_version 3.1.0-git0acbc11   
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
0      ZhaoEtAl2006Asc() rjb rrup  vs30       hypo_depth mag rake
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
1         PointSource  6            0.10253   0.0        389       20        40    
========= ============ ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
PointSource  0.10253   1     
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =========
operation-duration mean    stddev  min     max     num_tasks
prefilter          0.00400 0.00185 0.00133 0.00660 20       
compute_ruptures   0.11093 NaN     0.11093 0.11093 1        
================== ======= ======= ======= ======= =========

Informational data
------------------
================ ======================================================================== ========
task             sent                                                                     received
prefilter        srcs=27.24 KB monitor=6.31 KB srcfilter=4.47 KB                          29.62 KB
compute_ruptures sources=5.71 KB src_filter=3.87 KB param=557 B monitor=330 B gsims=119 B 7.51 KB 
================ ======================================================================== ========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
managing sources               0.20872   0.0       1     
total compute_ruptures         0.11093   2.92969   1     
total prefilter                0.08009   3.37109   20    
reading composite source model 0.01070   0.0       1     
store source_info              0.00822   0.0       1     
saving ruptures                0.00760   0.0       1     
splitting sources              0.00632   0.0       1     
making contexts                0.00542   0.0       3     
reading site collection        0.00379   0.0       1     
setting event years            0.00246   0.0       1     
unpickling prefilter           0.00177   0.0       20    
unpickling compute_ruptures    3.266E-04 0.0       1     
============================== ========= ========= ======