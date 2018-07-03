Event Based Risk SJ
===================

============== ===================
checksum32     2,235,537,411      
date           2018-06-26T14:58:20
engine_version 3.2.0-gitb0cd949   
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
1         PointSource  6            0.07801   0.0        19        20        26    
========= ============ ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
PointSource  0.07801   1     
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =========
operation-duration mean    stddev  min     max     num_tasks
RtreeFilter        0.00468 0.00165 0.00167 0.00712 20       
compute_hazard     0.04875 0.03136 0.02658 0.07093 2        
================== ======= ======= ======= ======= =========

Data transfer
-------------
============== ============================================================================================ ========
task           sent                                                                                         received
RtreeFilter    srcs=27.24 KB monitor=6.29 KB srcfilter=5.45 KB                                              29.62 KB
compute_hazard sources_or_ruptures=14.08 KB param=4.43 KB monitor=644 B rlzs_by_gsim=578 B src_filter=492 B 5.83 KB 
============== ============================================================================================ ========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total compute_hazard           0.09751   7.59375   2     
total prefilter                0.09366   3.15625   20    
managing sources               0.09356   0.0       1     
building ruptures              0.09067   6.74219   2     
reading composite source model 0.01059   0.0       1     
unpickling prefilter           0.00671   0.0       20    
splitting sources              0.00641   0.0       1     
store source_info              0.00577   0.0       1     
saving ruptures                0.00487   0.0       2     
reading site collection        0.00370   0.0       1     
making contexts                0.00160   0.0       3     
unpickling compute_hazard      8.245E-04 0.0       2     
GmfGetter.init                 7.284E-04 0.0       2     
aggregating hcurves            4.039E-04 0.0       2     
============================== ========= ========= ======