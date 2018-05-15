Event Based Hazard
==================

============== ===================
checksum32     427,751,893        
date           2018-05-15T04:12:55
engine_version 3.1.0-git0acbc11   
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
0      SadighEtAl1997() rjb rrup  vs30       mag rake  
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
3         SimpleFaultSource         2            0.32797   0.0        15        15        13    
1         CharacteristicFaultSource 1            5.157E-04 0.0        1         1         0     
========= ========================= ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
========================= ========= ======
source_class              calc_time counts
========================= ========= ======
CharacteristicFaultSource 5.157E-04 1     
SimpleFaultSource         0.32797   1     
========================= ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =========
operation-duration mean    stddev  min     max     num_tasks
prefilter          0.00807 0.00141 0.00457 0.00966 16       
compute_ruptures   0.06110 0.03331 0.02711 0.10649 6        
================== ======= ======= ======= ======= =========

Informational data
------------------
================ ============================================================================ ========
task             sent                                                                         received
prefilter        srcs=30.22 KB monitor=5.05 KB srcfilter=3.58 KB                              30.86 KB
compute_ruptures sources=21.13 KB src_filter=4.2 KB param=3.74 KB monitor=1.93 KB gsims=720 B 11.99 KB
================ ============================================================================ ========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total compute_ruptures         0.36660   4.69531   6     
managing sources               0.16873   0.0       1     
total prefilter                0.12909   5.07031   16    
making contexts                0.01770   0.0       5     
reading composite source model 0.01467   0.0       1     
saving ruptures                0.00594   0.0       6     
store source_info              0.00355   0.0       1     
reading site collection        0.00297   0.0       1     
setting event years            0.00137   0.0       1     
unpickling prefilter           0.00103   0.0       16    
splitting sources              5.813E-04 0.0       1     
unpickling compute_ruptures    5.708E-04 0.0       6     
reading exposure               3.781E-04 0.0       1     
============================== ========= ========= ======