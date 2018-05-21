CGS2017 PSHA model (Colombia), EventBased PSHA - test -  v.1 - 2018/02/11
=========================================================================

============== ===================
checksum32     3,691,355,175      
date           2018-05-15T04:14:28
engine_version 3.1.0-git0acbc11   
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
========= ======= ================ ================
smlt_path weight  gsim_logic_tree  num_realizations
========= ======= ================ ================
b1        1.00000 trivial(0,1,0,0) 1/1             
========= ======= ================ ================

Required parameters per tectonic region type
--------------------------------------------
====== ======================= ========= ============ ==============
grp_id gsims                   distances siteparams   ruptparams    
====== ======================= ========= ============ ==============
0      MontalvaEtAl2016SSlab() rhypo rjb backarc vs30 hypo_depth mag
1      MontalvaEtAl2016SSlab() rhypo rjb backarc vs30 hypo_depth mag
====== ======================= ========= ============ ==============

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=2, rlzs=1)
  0,MontalvaEtAl2016SSlab(): [0]
  1,MontalvaEtAl2016SSlab(): [0]>

Number of ruptures per tectonic region type
-------------------------------------------
======================================= ====== =============== ============ ============
source_model                            grp_id trt             eff_ruptures tot_ruptures
======================================= ====== =============== ============ ============
slab_buc0/6.05.nrml slab_buc1/6.75.nrml 0      Deep Seismicity 15           7           
slab_buc0/6.05.nrml slab_buc1/6.75.nrml 1      Deep Seismicity 15           8           
======================================= ====== =============== ============ ============

============= ==
#TRT models   2 
#eff_ruptures 30
#tot_ruptures 15
#tot_weight   15
============= ==

Slowest sources
---------------
========= ========================== ============ ========= ========== ========= ========= ======
source_id source_class               num_ruptures calc_time split_time num_sites num_split events
========= ========================== ============ ========= ========== ========= ========= ======
buc06pt05 NonParametricSeismicSource 7            1.800E-04 3.266E-05  14        14        0     
buc16pt75 NonParametricSeismicSource 8            1.214E-04 2.122E-05  16        16        0     
========= ========================== ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
========================== ========= ======
source_class               calc_time counts
========================== ========= ======
NonParametricSeismicSource 3.014E-04 2     
========================== ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =========
operation-duration mean    stddev  min     max     num_tasks
prefilter          0.00483 0.00131 0.00292 0.00823 15       
count_ruptures     0.00265 NaN     0.00265 0.00265 1        
================== ======= ======= ======= ======= =========

Fastest task
------------
taskno=1, weight=15, duration=0 s, sources="buc06pt05 buc16pt75"

======== ======= ====== ======= ======= ==
variable mean    stddev min     max     n 
======== ======= ====== ======= ======= ==
nsites   1.00000 0.0    1       1       15
weight   1.00000 0.0    1.00000 1.00000 15
======== ======= ====== ======= ======= ==

Slowest task
------------
taskno=1, weight=15, duration=0 s, sources="buc06pt05 buc16pt75"

======== ======= ====== ======= ======= ==
variable mean    stddev min     max     n 
======== ======= ====== ======= ======= ==
nsites   1.00000 0.0    1       1       15
weight   1.00000 0.0    1.00000 1.00000 15
======== ======= ====== ======= ======= ==

Informational data
------------------
============== ====================================================================== ========
task           sent                                                                   received
prefilter      srcs=22.65 KB monitor=4.78 KB srcfilter=3.35 KB                        23.25 KB
count_ruptures sources=15.12 KB srcfilter=717 B param=542 B monitor=333 B gsims=129 B 451 B   
============== ====================================================================== ========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total prefilter                0.07244   3.41016   15    
managing sources               0.06064   0.0       1     
reading composite source model 0.01165   0.0       1     
store source_info              0.00476   0.0       1     
total count_ruptures           0.00265   0.00391   1     
unpickling prefilter           0.00124   0.0       15    
splitting sources              5.646E-04 0.0       1     
reading site collection        3.393E-04 0.0       1     
unpickling count_ruptures      4.172E-05 0.0       1     
saving probability maps        3.552E-05 0.0       1     
aggregate curves               3.171E-05 0.0       1     
============================== ========= ========= ======