CGS2017 PSHA model (Colombia), EventBased PSHA - test -  v.1 - 2018/02/11
=========================================================================

============== ===================
checksum32     420,579,279        
date           2018-03-01T10:45:06
engine_version 2.10.0-git18f5063  
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
b1        1.000  trivial(0,1,0,0) 1/1             
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

Informational data
------------------
========================== ==========================================================================
count_ruptures.received    tot 457 B, max_per_task 457 B                                             
count_ruptures.sent        sources 12.99 KB, srcfilter 722 B, param 548 B, monitor 330 B, gsims 129 B
hostname                   tstation.gem.lan                                                          
========================== ==========================================================================

Slowest sources
---------------
========= ========================== ============ ========= ========= =========
source_id source_class               num_ruptures calc_time num_sites num_split
========= ========================== ============ ========= ========= =========
buc16pt75 NonParametricSeismicSource 8            0.029     17        16       
buc06pt05 NonParametricSeismicSource 7            0.024     15        14       
========= ========================== ============ ========= ========= =========

Computation times by source typology
------------------------------------
========================== ========= ======
source_class               calc_time counts
========================== ========= ======
NonParametricSeismicSource 0.053     2     
========================== ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
count_ruptures     0.055 NaN    0.055 0.055 1        
================== ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total count_ruptures           0.055     0.117     1     
managing sources               0.030     0.0       1     
reading composite source model 0.015     0.0       1     
store source_info              0.006     0.0       1     
reading site collection        7.510E-05 0.0       1     
unpickling count_ruptures      5.841E-05 0.0       1     
aggregate curves               3.767E-05 0.0       1     
saving probability maps        3.743E-05 0.0       1     
============================== ========= ========= ======