Event Based Hazard QA Test, Case 17
===================================

============== ===================
checksum32     2,756,942,605      
date           2018-06-26T14:58:12
engine_version 3.2.0-gitb0cd949   
============== ===================

num_sites = 1, num_levels = 3

Parameters
----------
=============================== ==================
calculation_mode                'event_based'     
number_of_logic_tree_samples    5                 
maximum_distance                {'default': 200.0}
investigation_time              1.0               
ses_per_logic_tree_path         3                 
truncation_level                2.0               
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                1.0               
area_source_discretization      20.0              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     106               
master_seed                     0                 
ses_seed                        106               
=============================== ==================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gsim_logic_tree.xml <gsim_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
source                  `source_model_1.xml <source_model_1.xml>`_                  
source                  `source_model_2.xml <source_model_2.xml>`_                  
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
b1        0.20000 trivial(1)      3/1             
b2        0.20000 trivial(1)      2/1             
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================ ========= ========== ==========
grp_id gsims            distances siteparams ruptparams
====== ================ ========= ========== ==========
0      SadighEtAl1997() rrup      vs30       mag rake  
1      SadighEtAl1997() rrup      vs30       mag rake  
====== ================ ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=2, rlzs=5)
  0,SadighEtAl1997(): [0 1 2]
  1,SadighEtAl1997(): [3 4]>

Number of ruptures per tectonic region type
-------------------------------------------
================== ====== ==================== ============ ============
source_model       grp_id trt                  eff_ruptures tot_ruptures
================== ====== ==================== ============ ============
source_model_1.xml 0      Active Shallow Crust 39           39          
source_model_2.xml 1      Active Shallow Crust 7            7           
================== ====== ==================== ============ ============

============= ==
#TRT models   2 
#eff_ruptures 46
#tot_ruptures 46
#tot_weight   46
============= ==

Slowest sources
---------------
========= ============ ============ ========= ========== ========= ========= ======
source_id source_class num_ruptures calc_time split_time num_sites num_split events
========= ============ ============ ========= ========== ========= ========= ======
1         PointSource  39           0.01855   0.0        1.00000   1         0     
2         PointSource  7            0.00542   0.0        1.00000   1         13    
========= ============ ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
PointSource  0.02397   2     
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =========
operation-duration mean    stddev  min     max     num_tasks
RtreeFilter        0.00378 0.00126 0.00289 0.00468 2        
compute_hazard     0.02134 0.00474 0.01798 0.02469 2        
================== ======= ======= ======= ======= =========

Data transfer
-------------
============== =========================================================================================== ========
task           sent                                                                                        received
RtreeFilter    srcs=2.99 KB monitor=644 B srcfilter=558 B                                                  3.08 KB 
compute_hazard param=4.58 KB sources_or_ruptures=3.16 KB monitor=644 B rlzs_by_gsim=586 B src_filter=492 B 5.61 KB 
============== =========================================================================================== ========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
managing sources               0.05393   0.0       1     
total compute_hazard           0.04267   8.49219   2     
building ruptures              0.03328   7.17578   2     
total prefilter                0.00757   2.60156   2     
store source_info              0.00525   0.0       1     
saving ruptures                0.00520   0.0       2     
reading composite source model 0.00508   0.0       1     
building hazard                0.00488   0.46875   2     
saving gmfs                    0.00328   0.0       2     
saving gmf_data/indices        0.00146   0.0       1     
making contexts                9.997E-04 0.0       3     
unpickling compute_hazard      9.153E-04 0.0       2     
unpickling prefilter           6.351E-04 0.0       2     
GmfGetter.init                 5.610E-04 0.0       2     
reading site collection        4.103E-04 0.0       1     
aggregating hcurves            4.096E-04 0.0       2     
splitting sources              3.490E-04 0.0       1     
building hazard curves         2.227E-04 0.0       2     
============================== ========= ========= ======