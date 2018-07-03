event based hazard
==================

============== ===================
checksum32     3,637,986,905      
date           2018-06-26T14:57:21
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
ses_per_logic_tree_path         200               
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
deductibile     absolute
insurance_limit absolute
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
1         SimpleFaultSource 24           0.60407   0.0        1.00000   15        14    
========= ================= ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
================= ========= ======
source_class      calc_time counts
================= ========= ======
SimpleFaultSource 0.60407   1     
================= ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =========
operation-duration mean    stddev  min     max     num_tasks
RtreeFilter        0.00632 0.00160 0.00400 0.00923 15       
compute_hazard     0.11069 0.02259 0.07655 0.14113 6        
================== ======= ======= ======= ======= =========

Data transfer
-------------
============== =================================================================================================== ========
task           sent                                                                                                received
RtreeFilter    srcs=19.36 KB monitor=4.72 KB srcfilter=4.09 KB                                                     19.96 KB
compute_hazard param=14.33 KB sources_or_ruptures=13.54 KB monitor=1.89 KB rlzs_by_gsim=1.76 KB src_filter=1.44 KB 16.38 KB
============== =================================================================================================== ========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total compute_hazard           0.66416   9.13672   6     
building ruptures              0.64551   8.41016   6     
managing sources               0.18515   0.0       1     
total prefilter                0.09486   4.37109   15    
making contexts                0.02615   0.0       9     
saving ruptures                0.02338   0.0       6     
store source_info              0.00651   0.0       1     
reading composite source model 0.00565   0.0       1     
unpickling prefilter           0.00442   0.0       15    
unpickling compute_hazard      0.00328   0.0       6     
GmfGetter.init                 0.00226   0.05859   6     
aggregating hcurves            0.00175   0.0       6     
reading site collection        0.00129   0.0       1     
reading exposure               8.392E-04 0.0       1     
splitting sources              4.971E-04 0.0       1     
============================== ========= ========= ======