event based hazard
==================

============== ===================
checksum32     867,520,762        
date           2018-06-05T06:38:43
engine_version 3.2.0-git65c4735   
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
1         SimpleFaultSource 482          0.50706   2.229E-04  1.00000   15        14    
========= ================= ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
================= ========= ======
source_class      calc_time counts
================= ========= ======
SimpleFaultSource 0.50706   1     
================= ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =========
operation-duration mean    stddev  min     max     num_tasks
RtreeFilter        0.00689 0.00199 0.00207 0.01050 15       
compute_ruptures   0.09326 0.02831 0.06927 0.14015 6        
================== ======= ======= ======= ======= =========

Data transfer
-------------
================ ============================================================================= ========
task             sent                                                                          received
RtreeFilter      srcs=19.36 KB monitor=5.07 KB srcfilter=4.09 KB                               19.96 KB
compute_ruptures sources=13.66 KB param=3.38 KB monitor=2.07 KB src_filter=1.37 KB gsims=786 B 16.16 KB
================ ============================================================================= ========

Slowest operations
------------------
=============================== ========= ========= ======
operation                       time_sec  memory_mb counts
=============================== ========= ========= ======
total compute_ruptures          0.55954   8.66016   6     
EventBasedRuptureCalculator.run 0.43062   0.0       1     
managing sources                0.29811   0.0       1     
total prefilter                 0.10330   5.19141   15    
making contexts                 0.02698   0.0       9     
saving ruptures                 0.01713   0.0       6     
reading composite source model  0.00700   0.0       1     
unpickling prefilter            0.00542   0.0       15    
store source_info               0.00489   0.0       1     
unpickling compute_ruptures     0.00246   0.0       6     
reading site collection         0.00242   0.0       1     
setting event years             0.00145   0.0       1     
reading exposure                0.00129   0.0       1     
splitting sources               5.469E-04 0.0       1     
=============================== ========= ========= ======