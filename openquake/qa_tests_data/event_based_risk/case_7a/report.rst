event based hazard
==================

============== ===================
checksum32     393,625,889        
date           2018-06-26T14:57:20
engine_version 3.2.0-gitb0cd949   
============== ===================

num_sites = 1, num_levels = 1

Parameters
----------
=============================== ==================
calculation_mode                'event_based'     
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              1.0               
ses_per_logic_tree_path         100               
truncation_level                3.0               
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                0.1               
area_source_discretization      10.0              
ground_motion_correlation_model 'JB2009'          
minimum_intensity               {}                
random_seed                     24                
master_seed                     0                 
ses_seed                        42                
=============================== ==================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
exposure                `exposure_model.xml <exposure_model.xml>`_                  
gsim_logic_tree         `gsim_logic_tree.xml <gsim_logic_tree.xml>`_                
job_ini                 `job_h.ini <job_h.ini>`_                                    
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
source_model.xml 0      Active Shallow Crust 482          482         
================ ====== ==================== ============ ============

Exposure model
--------------
=============== ========
#assets         1       
#taxonomies     1       
deductibile     relative
insurance_limit relative
=============== ========

======== ======= ====== === === ========= ==========
taxonomy mean    stddev min max num_sites num_assets
tax1     1.00000 NaN    1   1   1         1         
======== ======= ====== === === ========= ==========

Slowest sources
---------------
========= ================= ============ ========= ========== ========= ========= ======
source_id source_class      num_ruptures calc_time split_time num_sites num_split events
========= ================= ============ ========= ========== ========= ========= ======
1         SimpleFaultSource 24           0.31561   0.0        1.00000   15        8     
========= ================= ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
================= ========= ======
source_class      calc_time counts
================= ========= ======
SimpleFaultSource 0.31561   1     
================= ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =========
operation-duration mean    stddev  min     max     num_tasks
RtreeFilter        0.00417 0.00167 0.00181 0.00683 15       
compute_hazard     0.06073 0.02051 0.03254 0.08900 6        
================== ======= ======= ======= ======= =========

Data transfer
-------------
============== =================================================================================================== ========
task           sent                                                                                                received
RtreeFilter    srcs=19.36 KB monitor=4.72 KB srcfilter=4.09 KB                                                     19.96 KB
compute_hazard param=13.76 KB sources_or_ruptures=13.54 KB monitor=1.89 KB rlzs_by_gsim=1.76 KB src_filter=1.44 KB 11.48 KB
============== =================================================================================================== ========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total compute_hazard           0.36439   9.13672   6     
building ruptures              0.34946   8.41016   6     
managing sources               0.11365   0.0       1     
total prefilter                0.06259   4.37109   15    
making contexts                0.01559   0.0       5     
saving ruptures                0.01333   0.0       6     
reading composite source model 0.00812   0.0       1     
unpickling prefilter           0.00541   0.0       15    
store source_info              0.00486   0.0       1     
reading site collection        0.00193   0.0       1     
unpickling compute_hazard      0.00193   0.0       6     
GmfGetter.init                 0.00178   0.0       6     
reading exposure               0.00123   0.0       1     
aggregating hcurves            0.00116   0.0       6     
splitting sources              6.726E-04 0.0       1     
============================== ========= ========= ======