event based two source models
=============================

============== ===================
checksum32     1,852,256,743      
date           2018-06-26T14:58:07
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
ses_per_logic_tree_path         2                 
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
======================== ==========================================================================
Name                     File                                                                      
======================== ==========================================================================
exposure                 `exposure_model.xml <exposure_model.xml>`_                                
gsim_logic_tree          `gsim_logic_tree.xml <gsim_logic_tree.xml>`_                              
job_ini                  `job_haz.ini <job_haz.ini>`_                                              
source                   `source_model_1.xml <source_model_1.xml>`_                                
source                   `source_model_2.xml <source_model_2.xml>`_                                
source_model_logic_tree  `source_model_logic_tree.xml <source_model_logic_tree.xml>`_              
structural_vulnerability `structural_vulnerability_model.xml <structural_vulnerability_model.xml>`_
======================== ==========================================================================

Composite source model
----------------------
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
b1        0.25000 trivial(1,1)    1/1             
b2        0.75000 trivial(1,1)    1/1             
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== =================== ========= ========== ==========
grp_id gsims               distances siteparams ruptparams
====== =================== ========= ========== ==========
0      BooreAtkinson2008() rjb       vs30       mag rake  
1      AkkarBommer2010()   rjb       vs30       mag rake  
2      BooreAtkinson2008() rjb       vs30       mag rake  
3      AkkarBommer2010()   rjb       vs30       mag rake  
====== =================== ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=4, rlzs=2)
  0,BooreAtkinson2008(): [0]
  1,AkkarBommer2010(): [0]
  2,BooreAtkinson2008(): [1]
  3,AkkarBommer2010(): [1]>

Number of ruptures per tectonic region type
-------------------------------------------
================== ====== ==================== ============ ============
source_model       grp_id trt                  eff_ruptures tot_ruptures
================== ====== ==================== ============ ============
source_model_1.xml 0      Active Shallow Crust 482          482         
source_model_1.xml 1      Stable Shallow Crust 4            4           
source_model_2.xml 2      Active Shallow Crust 482          482         
source_model_2.xml 3      Stable Shallow Crust 1            1           
================== ====== ==================== ============ ============

============= ===
#TRT models   4  
#eff_ruptures 969
#tot_ruptures 969
#tot_weight   969
============= ===

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
========= ========================= ============ ========= ========== ========= ========= ======
source_id source_class              num_ruptures calc_time split_time num_sites num_split events
========= ========================= ============ ========= ========== ========= ========= ======
1         SimpleFaultSource         24           0.45033   0.0        1.00000   30        1     
2         CharacteristicFaultSource 1            0.01129   0.0        1.00000   2         2     
========= ========================= ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
========================= ========= ======
source_class              calc_time counts
========================= ========= ======
CharacteristicFaultSource 0.01129   1     
SimpleFaultSource         0.45033   1     
========================= ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =========
operation-duration mean    stddev  min     max     num_tasks
RtreeFilter        0.00615 0.00272 0.00189 0.01263 32       
compute_hazard     0.04397 0.02285 0.01285 0.08462 14       
================== ======= ======= ======= ======= =========

Data transfer
-------------
============== ================================================================================================== ========
task           sent                                                                                               received
RtreeFilter    srcs=50.76 KB monitor=10.06 KB srcfilter=8.72 KB                                                   52.05 KB
compute_hazard param=43.38 KB sources_or_ruptures=39.28 KB monitor=4.4 KB rlzs_by_gsim=4.11 KB src_filter=3.36 KB 14.38 KB
============== ================================================================================================== ========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total compute_hazard           0.61565   10        14    
building ruptures              0.56087   8.41016   14    
total prefilter                0.19664   4.74219   32    
managing sources               0.19321   0.0       1     
reading composite source model 0.02445   0.0       1     
saving gmfs                    0.02020   0.0       14    
saving ruptures                0.01244   0.0       14    
building hazard                0.01213   0.46875   14    
unpickling prefilter           0.01124   0.0       32    
making contexts                0.00613   0.0       2     
store source_info              0.00543   0.0       1     
GmfGetter.init                 0.00449   0.18750   14    
unpickling compute_hazard      0.00423   0.0       14    
aggregating hcurves            0.00244   0.0       14    
saving gmf_data/indices        0.00175   0.0       1     
reading site collection        0.00130   0.0       1     
splitting sources              8.056E-04 0.0       1     
reading exposure               8.054E-04 0.0       1     
building hazard curves         4.301E-04 0.0       2     
============================== ========= ========= ======