event based hazard
==================

============== ===================
checksum32     2,235,846,578      
date           2018-05-15T04:13:02
engine_version 3.1.0-git0acbc11   
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
1         SimpleFaultSource 2            0.23535   0.0        15        15        12    
========= ================= ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
================= ========= ======
source_class      calc_time counts
================= ========= ======
SimpleFaultSource 0.23535   1     
================= ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =========
operation-duration mean    stddev  min     max     num_tasks
prefilter          0.00793 0.00151 0.00471 0.00998 15       
compute_ruptures   0.04477 0.01287 0.02711 0.05970 6        
================== ======= ======= ======= ======= =========

Informational data
------------------
================ ============================================================================ ========
task             sent                                                                         received
prefilter        srcs=19.36 KB monitor=4.73 KB srcfilter=3.35 KB                              19.96 KB
compute_ruptures sources=10.76 KB src_filter=4.2 KB param=3.26 KB monitor=1.93 KB gsims=786 B 11.81 KB
================ ============================================================================ ========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total compute_ruptures         0.26861   4.57422   6     
managing sources               0.12325   0.0       1     
total prefilter                0.11897   5.07031   15    
making contexts                0.01232   0.0       5     
saving ruptures                0.00639   0.0       6     
reading composite source model 0.00599   0.0       1     
store source_info              0.00356   0.0       1     
reading site collection        0.00192   0.0       1     
setting event years            0.00120   0.0       1     
reading exposure               0.00104   0.0       1     
unpickling prefilter           9.682E-04 0.0       15    
unpickling compute_ruptures    6.433E-04 0.0       6     
splitting sources              6.058E-04 0.0       1     
============================== ========= ========= ======