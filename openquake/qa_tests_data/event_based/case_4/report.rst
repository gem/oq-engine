Event-Based Hazard QA Test, Case 4
==================================

============== ===================
checksum32     530,652,814        
date           2018-06-26T14:58:21
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
ses_per_logic_tree_path         50                
truncation_level                0.0               
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
source_model.xml 0      Active Shallow Crust 5            5           
================ ====== ==================== ============ ============

Slowest sources
---------------
========= ================= ============ ========= ========== ========= ========= ======
source_id source_class      num_ruptures calc_time split_time num_sites num_split events
========= ================= ============ ========= ========== ========= ========= ======
1         SimpleFaultSource 5            0.00789   0.0        1.00000   1         56    
========= ================= ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
================= ========= ======
source_class      calc_time counts
================= ========= ======
SimpleFaultSource 0.00789   1     
================= ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ====== ======= ======= =========
operation-duration mean    stddev min     max     num_tasks
RtreeFilter        0.00243 NaN    0.00243 0.00243 1        
compute_hazard     0.02132 NaN    0.02132 0.02132 1        
================== ======= ====== ======= ======= =========

Data transfer
-------------
============== ========================================================================================== ========
task           sent                                                                                       received
RtreeFilter    srcs=0 B srcfilter=0 B monitor=0 B                                                         1.22 KB 
compute_hazard param=2.3 KB sources_or_ruptures=1.26 KB monitor=322 B rlzs_by_gsim=290 B src_filter=246 B 7.67 KB 
============== ========================================================================================== ========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
managing sources               0.05517   0.0       1     
total compute_hazard           0.02132   7.67969   1     
building ruptures              0.01427   6.80469   1     
store source_info              0.00596   0.0       1     
saving ruptures                0.00595   0.0       1     
reading composite source model 0.00404   0.0       1     
building hazard                0.00284   0.0       1     
saving gmfs                    0.00245   0.0       1     
total prefilter                0.00243   0.0       1     
saving gmf_data/indices        0.00175   0.0       1     
making contexts                0.00126   0.0       5     
unpickling compute_hazard      8.960E-04 0.0       1     
GmfGetter.init                 6.049E-04 0.0       1     
reading site collection        3.407E-04 0.0       1     
aggregating hcurves            2.964E-04 0.0       1     
splitting sources              2.944E-04 0.0       1     
unpickling prefilter           2.890E-04 0.0       1     
building hazard curves         2.222E-04 0.0       1     
============================== ========= ========= ======