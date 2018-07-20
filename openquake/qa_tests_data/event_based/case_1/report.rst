Event Based QA Test, Case 1
===========================

============== ===================
checksum32     691,939,853        
date           2018-06-26T14:58:36
engine_version 3.2.0-gitb0cd949   
============== ===================

num_sites = 1, num_levels = 3

Parameters
----------
=============================== ==================
calculation_mode                'event_based'     
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              1.0               
ses_per_logic_tree_path         2000              
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
b1        1.00000 trivial(1)      1/1             
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================ ========= ========== ==========
grp_id gsims            distances siteparams ruptparams
====== ================ ========= ========== ==========
0      SadighEtAl1997() rrup      vs30       mag rake  
====== ================ ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)
  0,SadighEtAl1997(): [0]>

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
1         PointSource  1            0.01537   0.0        1.00000   1         2,037 
========= ============ ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
PointSource  0.01537   1     
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ========= ====== ========= ========= =========
operation-duration mean      stddev min       max       num_tasks
RtreeFilter        8.130E-04 NaN    8.130E-04 8.130E-04 1        
compute_hazard     0.07215   NaN    0.07215   0.07215   1        
================== ========= ====== ========= ========= =========

Data transfer
-------------
============== =========================================================================================== ========
task           sent                                                                                        received
RtreeFilter    srcs=0 B srcfilter=0 B monitor=0 B                                                          1.29 KB 
compute_hazard param=2.29 KB sources_or_ruptures=1.32 KB monitor=322 B rlzs_by_gsim=290 B src_filter=246 B 90.05 KB
============== =========================================================================================== ========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
managing sources               0.11870   0.0       1     
total compute_hazard           0.07215   8.18359   1     
building hazard                0.04448   0.53125   1     
building ruptures              0.02153   6.86719   1     
saving ruptures                0.01907   0.0       1     
store source_info              0.00613   0.0       1     
saving gmfs                    0.00269   0.0       1     
reading composite source model 0.00209   0.0       1     
saving gmf_data/indices        0.00176   0.0       1     
GmfGetter.init                 8.173E-04 0.0       1     
total prefilter                8.130E-04 0.0       1     
unpickling compute_hazard      7.732E-04 0.0       1     
making contexts                6.800E-04 0.0       1     
unpickling prefilter           4.706E-04 0.0       1     
reading site collection        3.138E-04 0.0       1     
aggregating hcurves            3.042E-04 0.0       1     
splitting sources              2.763E-04 0.0       1     
building hazard curves         2.606E-04 0.0       1     
============================== ========= ========= ======