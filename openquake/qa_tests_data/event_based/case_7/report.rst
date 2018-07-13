Event-based PSHA with logic tree sampling
=========================================

============== ===================
checksum32     3,756,725,912      
date           2018-06-26T14:58:28
engine_version 3.2.0-gitb0cd949   
============== ===================

num_sites = 3, num_levels = 38

Parameters
----------
=============================== ==================
calculation_mode                'event_based'     
number_of_logic_tree_samples    10                
maximum_distance                {'default': 200.0}
investigation_time              50.0              
ses_per_logic_tree_path         40                
truncation_level                3.0               
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                0.2               
area_source_discretization      20.0              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     23                
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
b11       0.10000 simple(3)       4/3             
b12       0.10000 simple(3)       6/3             
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

  <RlzsAssoc(size=5, rlzs=10)
  0,BooreAtkinson2008(): [1]
  0,CampbellBozorgnia2008(): [2]
  0,ChiouYoungs2008(): [0 3]
  1,BooreAtkinson2008(): [4 5 6 7 9]
  1,CampbellBozorgnia2008(): [8]>

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
1         PointSource  8            12        0.0        2.05863   614       49,186
========= ============ ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
PointSource  12        1     
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =========
operation-duration mean    stddev  min     max     num_tasks
RtreeFilter        0.00703 0.00261 0.00296 0.01679 56       
compute_hazard     0.68970 0.31164 0.25937 1.09428 62       
================== ======= ======= ======= ======= =========

Data transfer
-------------
============== ======================================================================================================= =========
task           sent                                                                                                    received 
RtreeFilter    srcs=209.74 KB monitor=17.61 KB srcfilter=15.26 KB                                                      238.34 KB
compute_hazard sources_or_ruptures=277.75 KB param=209.01 KB rlzs_by_gsim=30.21 KB monitor=19.5 KB src_filter=14.89 KB 4.14 MB  
============== ======================================================================================================= =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total compute_hazard           42        8.39453   62    
building hazard                29        1.29297   62    
building ruptures              12        6.95312   62    
making contexts                3.12108   0.0       2,667 
managing sources               2.81319   0.0       1     
saving ruptures                0.40709   0.0       62    
total prefilter                0.39354   3.15625   56    
unpickling compute_hazard      0.30538   0.0       62    
GmfGetter.init                 0.25371   0.06250   62    
building hazard curves         0.16819   0.0       798   
splitting sources              0.14909   0.0       1     
reading composite source model 0.14595   0.0       1     
saving gmfs                    0.14177   0.0       62    
aggregating hcurves            0.05491   0.0       62    
unpickling prefilter           0.03459   0.0       56    
store source_info              0.00474   0.0       1     
saving gmf_data/indices        0.00163   0.0       1     
reading site collection        3.688E-04 0.0       1     
============================== ========= ========= ======