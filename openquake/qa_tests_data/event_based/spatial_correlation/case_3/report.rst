Probabilistic Event-Based QA Test with No Spatial Correlation, case 3
=====================================================================

============== ===================
checksum32     3,678,589,439      
date           2018-06-26T14:58:19
engine_version 3.2.0-gitb0cd949   
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
1         PointSource  1            0.03771   0.0        2.00000   1         45,319
========= ============ ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
PointSource  0.03771   1     
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ========= ====== ========= ========= =========
operation-duration mean      stddev min       max       num_tasks
RtreeFilter        9.127E-04 NaN    9.127E-04 9.127E-04 1        
compute_hazard     0.26858   NaN    0.26858   0.26858   1        
================== ========= ====== ========= ========= =========

Data transfer
-------------
============== =========================================================================================== ========
task           sent                                                                                        received
RtreeFilter    srcs=0 B srcfilter=0 B monitor=0 B                                                          1.28 KB 
compute_hazard param=2.28 KB sources_or_ruptures=1.32 KB monitor=322 B rlzs_by_gsim=301 B src_filter=246 B 1.47 MB 
============== =========================================================================================== ========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
managing sources               0.30708   1.36328   1     
total compute_hazard           0.26858   9.17188   1     
building ruptures              0.04234   8.50391   1     
store source_info              0.00903   0.0       1     
GmfGetter.init                 0.00869   0.0       1     
reading composite source model 0.00277   0.0       1     
unpickling compute_hazard      0.00254   0.0       1     
total prefilter                9.127E-04 0.0       1     
making contexts                7.727E-04 0.0       1     
saving ruptures                5.457E-04 0.0       1     
reading site collection        3.865E-04 0.0       1     
aggregating hcurves            3.395E-04 0.0       1     
splitting sources              3.176E-04 0.0       1     
unpickling prefilter           3.104E-04 0.0       1     
============================== ========= ========= ======