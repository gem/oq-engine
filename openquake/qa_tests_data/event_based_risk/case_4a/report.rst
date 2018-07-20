Event Based Hazard
==================

============== ===================
checksum32     2,621,435,700      
date           2018-06-26T14:57:13
engine_version 3.2.0-gitb0cd949   
============== ===================

num_sites = 1, num_levels = 11

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
area_source_discretization      20.0              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     24                
master_seed                     0                 
ses_seed                        42                
=============================== ==================

Input files
-----------
======================== ==========================================================================
Name                     File                                                                      
======================== ==========================================================================
exposure                 `exposure_model.xml <exposure_model.xml>`_                                
gsim_logic_tree          `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                              
job_ini                  `job_hazard.ini <job_hazard.ini>`_                                        
site_model               `site_model.xml <site_model.xml>`_                                        
source                   `source_model.xml <source_model.xml>`_                                    
source_model_logic_tree  `source_model_logic_tree.xml <source_model_logic_tree.xml>`_              
structural_vulnerability `structural_vulnerability_model.xml <structural_vulnerability_model.xml>`_
======================== ==========================================================================

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
source_model.xml 0      Active Shallow Crust 483          483         
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
Wood     1.00000 NaN    1   1   1         1         
======== ======= ====== === === ========= ==========

Slowest sources
---------------
========= ========================= ============ ========= ========== ========= ========= ======
source_id source_class              num_ruptures calc_time split_time num_sites num_split events
========= ========================= ============ ========= ========== ========= ========= ======
3         SimpleFaultSource         24           0.38203   0.0        1.00000   15        9     
1         CharacteristicFaultSource 1            0.00129   0.0        1.00000   1         0     
========= ========================= ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
========================= ========= ======
source_class              calc_time counts
========================= ========= ======
CharacteristicFaultSource 0.00129   1     
SimpleFaultSource         0.38203   1     
========================= ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =========
operation-duration mean    stddev  min     max     num_tasks
RtreeFilter        0.00623 0.00205 0.00258 0.00936 16       
compute_hazard     0.07228 0.01358 0.04744 0.08445 6        
================== ======= ======= ======= ======= =========

Data transfer
-------------
============== ================================================================================================= ========
task           sent                                                                                              received
RtreeFilter    srcs=30.22 KB monitor=5.03 KB srcfilter=4.36 KB                                                   30.86 KB
compute_hazard sources_or_ruptures=24.06 KB param=15.8 KB monitor=1.89 KB rlzs_by_gsim=1.7 KB src_filter=1.44 KB 14.55 KB
============== ================================================================================================= ========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total compute_hazard           0.43366   7.68359   6     
building ruptures              0.41849   7.01562   6     
managing sources               0.11952   0.00391   1     
total prefilter                0.09962   4.74219   16    
reading composite source model 0.01580   0.0       1     
saving ruptures                0.01053   0.00391   6     
unpickling prefilter           0.00451   0.0       16    
store source_info              0.00420   0.0       1     
making contexts                0.00201   0.0       5     
reading site collection        0.00190   0.0       1     
GmfGetter.init                 0.00183   0.15625   6     
unpickling compute_hazard      0.00164   0.0       6     
aggregating hcurves            0.00148   0.0       6     
reading exposure               5.922E-04 0.0       1     
splitting sources              4.907E-04 0.0       1     
============================== ========= ========= ======