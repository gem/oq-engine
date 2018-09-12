Event-based PSHA producing hazard curves only
=============================================

============== ===================
checksum32     3,219,914,866      
date           2018-09-05T10:03:51
engine_version 3.2.0-gitb4ef3a4b6c
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

============= =====
#TRT models   2    
#eff_ruptures 4,912
#tot_ruptures 4,912
#tot_weight   0    
============= =====

Slowest sources
---------------
========= ============ ============ ========= ========== ========= ========= ======
source_id source_class num_ruptures calc_time split_time num_sites num_split events
========= ============ ============ ========= ========== ========= ========= ======
1         AreaSource   2,456        13        0.05692    1.00000   614       16,186
========= ============ ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
AreaSource   13        1     
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
==================== ======= ========= ======= ======= =========
operation-duration   mean    stddev    min     max     num_tasks
pickle_source_models 0.06979 4.983E-04 0.06944 0.07014 2        
preprocess           0.22679 0.03585   0.11687 0.30604 62       
compute_gmfs         0.32593 0.05134   0.09480 0.40984 64       
==================== ======= ========= ======= ======= =========

Data transfer
-------------
==================== ====================================================================================================== ========
task                 sent                                                                                                   received
pickle_source_models monitor=618 B converter=578 B fnames=368 B                                                             318 B   
preprocess           srcs=219.21 KB param=29.43 KB monitor=19.31 KB srcfilter=15.32 KB                                      3.95 MB 
compute_gmfs         sources_or_ruptures=3.97 MB param=164.69 KB rlzs_by_gsim=34.62 KB monitor=19.19 KB src_filter=13.75 KB 4.52 MB 
==================== ====================================================================================================== ========

Slowest operations
------------------
========================== ======== ========= ======
operation                  time_sec memory_mb counts
========================== ======== ========= ======
total compute_gmfs         20       0.48438   64    
building hazard            20       0.48438   64    
total preprocess           14       0.46094   62    
making contexts            3.22762  0.0       3,081 
saving ruptures            2.22989  1.02734   613   
GmfGetter.init             0.27155  0.12109   64    
managing sources           0.25419  3.85938   1     
building ruptures          0.17543  0.0       64    
saving gmfs                0.14207  0.0       64    
total pickle_source_models 0.13958  1.01953   2     
splitting sources          0.11546  0.0       1     
building hazard curves     0.02538  0.0       192   
aggregating hcurves        0.01961  0.0       64    
store source_info          0.00448  0.0       1     
saving gmf_data/indices    0.00118  1.02734   1     
========================== ======== ========= ======