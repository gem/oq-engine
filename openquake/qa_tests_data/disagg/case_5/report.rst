CGS2017 PSHA model (Colombia), EventBased PSHA - test -  v.1 - 2018/02/11
=========================================================================

============== ===================
checksum32     3,691,355,175      
date           2018-03-26T15:57:47
engine_version 2.10.0-git543cfb0  
============== ===================

num_sites = 1, num_levels = 19

Parameters
----------
=============================== ==================
calculation_mode                'disaggregation'  
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              1.0               
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                0.1               
area_source_discretization      5.0               
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     1024              
master_seed                     0                 
ses_seed                        42                
=============================== ==================

Input files
-----------
======================= ======================================================================================================
Name                    File                                                                                                  
======================= ======================================================================================================
gsim_logic_tree         `gmpe_lt_col_2016_pga_EB.xml <gmpe_lt_col_2016_pga_EB.xml>`_                                          
job_ini                 `job.ini <job.ini>`_                                                                                  
source                  `6.05.nrml <6.05.nrml>`_                                                                              
source                  `6.75.nrml <6.75.nrml>`_                                                                              
source_model_logic_tree `source_model_lt_col18_full_model_S_test_slab.xml <source_model_lt_col18_full_model_S_test_slab.xml>`_
======================= ======================================================================================================

Composite source model
----------------------
========= ====== ================ ================
smlt_path weight gsim_logic_tree  num_realizations
========= ====== ================ ================
b1        1.000  trivial(1,0,0,0) 1/1             
========= ====== ================ ================

Required parameters per tectonic region type
--------------------------------------------
====== ======================= ========= ============ ==============
grp_id gsims                   distances siteparams   ruptparams    
====== ======================= ========= ============ ==============
0      MontalvaEtAl2016SSlab() rhypo     backarc vs30 hypo_depth mag
1      MontalvaEtAl2016SSlab() rhypo     backarc vs30 hypo_depth mag
====== ======================= ========= ============ ==============

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=2, rlzs=1)
  0,MontalvaEtAl2016SSlab(): [0]
  1,MontalvaEtAl2016SSlab(): [0]>

Number of ruptures per tectonic region type
-------------------------------------------
========================================================= ====== =============== ============ ============
source_model                                              grp_id trt             eff_ruptures tot_ruptures
========================================================= ====== =============== ============ ============
slab_buc0/6.05.nrml
                  slab_buc1/6.75.nrml 0      Deep Seismicity 15           7           
slab_buc0/6.05.nrml
                  slab_buc1/6.75.nrml 1      Deep Seismicity 15           8           
========================================================= ====== =============== ============ ============

============= ==
#TRT models   2 
#eff_ruptures 30
#tot_ruptures 15
#tot_weight   15
============= ==

Slowest sources
---------------
========= ========================== ============ ========= ========== ========= =========
source_id source_class               num_ruptures calc_time split_time num_sites num_split
========= ========================== ============ ========= ========== ========= =========
buc06pt05 NonParametricSeismicSource 7            0.022     4.387E-05  14        14       
buc16pt75 NonParametricSeismicSource 8            0.020     3.743E-05  16        16       
========= ========================== ============ ========= ========== ========= =========

Computation times by source typology
------------------------------------
========================== ========= ======
source_class               calc_time counts
========================== ========= ======
NonParametricSeismicSource 0.041     2     
========================== ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
count_ruptures     0.044 NaN    0.044 0.044 1        
================== ===== ====== ===== ===== =========

Informational data
------------------
============== ====================================================================== ========
task           sent                                                                   received
count_ruptures sources=12.99 KB srcfilter=722 B param=548 B monitor=330 B gsims=129 B 457 B   
============== ====================================================================== ========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total count_ruptures           0.044     3.629     1     
managing sources               0.026     0.0       1     
reading composite source model 0.015     0.0       1     
store source_info              0.004     0.0       1     
splitting sources              5.741E-04 0.0       1     
reading site collection        2.267E-04 0.0       1     
unpickling count_ruptures      6.437E-05 0.0       1     
aggregate curves               3.219E-05 0.0       1     
saving probability maps        3.028E-05 0.0       1     
============================== ========= ========= ======