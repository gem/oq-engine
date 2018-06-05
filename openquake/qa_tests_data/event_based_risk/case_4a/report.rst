Event Based Hazard
==================

============== ===================
checksum32     427,751,893        
date           2018-06-05T06:38:35
engine_version 3.2.0-git65c4735   
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
3         SimpleFaultSource         482          0.35058   1.805E-04  1.00000   15        9     
1         CharacteristicFaultSource 1            0.00157   3.338E-06  1.00000   1         0     
========= ========================= ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
========================= ========= ======
source_class              calc_time counts
========================= ========= ======
CharacteristicFaultSource 0.00157   1     
SimpleFaultSource         0.35058   1     
========================= ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =========
operation-duration mean    stddev  min     max     num_tasks
RtreeFilter        0.00631 0.00178 0.00203 0.00903 16       
compute_ruptures   0.06705 0.02435 0.03733 0.10348 6        
================== ======= ======= ======= ======= =========

Data transfer
-------------
================ ============================================================================= ========
task             sent                                                                          received
RtreeFilter      srcs=30.22 KB monitor=5.41 KB srcfilter=4.36 KB                               30.86 KB
compute_ruptures sources=24.17 KB param=3.86 KB monitor=2.07 KB src_filter=1.37 KB gsims=720 B 14.33 KB
================ ============================================================================= ========

Slowest operations
------------------
=============================== ========= ========= ======
operation                       time_sec  memory_mb counts
=============================== ========= ========= ======
EventBasedRuptureCalculator.run 0.41779   0.0       1     
total compute_ruptures          0.40230   7.19531   6     
managing sources                0.24878   0.0       1     
total prefilter                 0.10101   5.19141   16    
reading composite source model  0.01493   0.0       1     
saving ruptures                 0.01092   0.0       6     
store source_info               0.00447   0.0       1     
unpickling prefilter            0.00440   0.0       16    
reading site collection         0.00220   0.0       1     
making contexts                 0.00203   0.0       5     
unpickling compute_ruptures     0.00203   0.0       6     
setting event years             0.00135   0.0       1     
reading exposure                5.350E-04 0.0       1     
splitting sources               4.544E-04 0.0       1     
=============================== ========= ========= ======