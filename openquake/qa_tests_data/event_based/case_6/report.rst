Event-based PSHA producing hazard curves only
=============================================

============== ===================
checksum32     3,219,914,866      
date           2018-06-26T14:58:15
engine_version 3.2.0-gitb0cd949   
============== ===================

num_sites = 1, num_levels = 5

Parameters
----------
=============================== ==================
calculation_mode                'event_based'     
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              50.0              
ses_per_logic_tree_path         300               
truncation_level                3.0               
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                0.2               
area_source_discretization      20.0              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     42                
master_seed                     0                 
ses_seed                        23                
=============================== ==================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
source                  `source_model1.xml <source_model1.xml>`_                    
source                  `source_model2.xml <source_model2.xml>`_                    
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
b11       0.60000 simple(3)       3/3             
b12       0.40000 simple(3)       3/3             
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ============================================================= =========== ============================= =================
grp_id gsims                                                         distances   siteparams                    ruptparams       
====== ============================================================= =========== ============================= =================
0      BooreAtkinson2008() CampbellBozorgnia2008() ChiouYoungs2008() rjb rrup rx vs30 vs30measured z1pt0 z2pt5 dip mag rake ztor
1      BooreAtkinson2008() CampbellBozorgnia2008() ChiouYoungs2008() rjb rrup rx vs30 vs30measured z1pt0 z2pt5 dip mag rake ztor
====== ============================================================= =========== ============================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=6, rlzs=6)
  0,BooreAtkinson2008(): [0]
  0,CampbellBozorgnia2008(): [1]
  0,ChiouYoungs2008(): [2]
  1,BooreAtkinson2008(): [3]
  1,CampbellBozorgnia2008(): [4]
  1,ChiouYoungs2008(): [5]>

Number of ruptures per tectonic region type
-------------------------------------------
================= ====== ==================== ============ ============
source_model      grp_id trt                  eff_ruptures tot_ruptures
================= ====== ==================== ============ ============
source_model1.xml 0      Active Shallow Crust 2,456        2,456       
source_model2.xml 1      Active Shallow Crust 2,456        2,456       
================= ====== ==================== ============ ============

============= ======
#TRT models   2     
#eff_ruptures 4,912 
#tot_ruptures 4,912 
#tot_weight   14,736
============= ======

Slowest sources
---------------
========= ============ ============ ========= ========== ========= ========= ======
source_id source_class num_ruptures calc_time split_time num_sites num_split events
========= ============ ============ ========= ========== ========= ========= ======
1         PointSource  8            14        0.0        1.00000   614       87,747
========= ============ ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
PointSource  14        1     
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =========
operation-duration mean    stddev  min     max     num_tasks
RtreeFilter        0.00514 0.00175 0.00212 0.00888 56       
compute_hazard     0.58219 0.21357 0.23551 0.91865 62       
================== ======= ======= ======= ======= =========

Data transfer
-------------
============== ======================================================================================================= ========
task           sent                                                                                                    received
RtreeFilter    srcs=209.74 KB monitor=17.61 KB srcfilter=15.26 KB                                                      235.8 KB
compute_hazard sources_or_ruptures=275.21 KB param=160.33 KB rlzs_by_gsim=33.54 KB monitor=19.5 KB src_filter=14.89 KB 5.13 MB 
============== ======================================================================================================= ========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total compute_hazard           36        8.33203   62    
building hazard                20        0.53125   62    
building ruptures              14        6.95312   62    
making contexts                3.45594   0.0       3,081 
managing sources               2.37770   0.25000   1     
saving ruptures                0.43243   0.0       62    
total prefilter                0.28758   1.26562   56    
GmfGetter.init                 0.25789   0.06250   62    
unpickling compute_hazard      0.23026   0.0       62    
saving gmfs                    0.12980   0.0       62    
splitting sources              0.11860   0.0       1     
reading composite source model 0.11578   0.0       1     
unpickling prefilter           0.02712   0.0       56    
building hazard curves         0.02470   0.0       186   
aggregating hcurves            0.01662   0.0       62    
store source_info              0.00458   0.0       1     
saving gmf_data/indices        0.00124   0.0       1     
reading site collection        2.620E-04 0.0       1     
============================== ========= ========= ======