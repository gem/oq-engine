CGS2017 PSHA model (Colombia), EventBased PSHA - test -  v.1 - 2018/02/11
=========================================================================

============== ===================
checksum32     3,691,355,175      
date           2018-09-25T14:27:45
engine_version 3.3.0-git8ffb37de56
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
====== ======================= ========== ============ ==============
grp_id gsims                   distances  siteparams   ruptparams    
====== ======================= ========== ============ ==============
0      MontalvaEtAl2016SSlab() rhypo rrup backarc vs30 hypo_depth mag
1      MontalvaEtAl2016SSlab() rhypo rrup backarc vs30 hypo_depth mag
====== ======================= ========== ============ ==============

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
slab_buc0/6.05.nrml slab_buc1/6.75.nrml 0      Deep Seismicity 7            7           
slab_buc0/6.05.nrml slab_buc1/6.75.nrml 1      Deep Seismicity 8            8           
======================================= ====== =============== ============ ============

============= ==
#TRT models   2 
#eff_ruptures 15
#tot_ruptures 15
#tot_weight   15
============= ==

Slowest sources
---------------
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= =======
grp_id source_id code gidx1 gidx2 num_ruptures calc_time split_time num_sites num_split weight 
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= =======
0      buc06pt05 N    0     76    7            0.00874   5.307E-04  7.00000   7         7.00000
1      buc16pt75 N    0     240   8            0.00501   4.063E-04  8.00000   8         8.00000
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= =======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
N    0.01375   2     
==== ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =========
operation-duration mean    stddev  min     max     num_tasks
read_source_models 0.00777 0.00200 0.00635 0.00918 2        
split_filter       0.00540 NaN     0.00540 0.00540 1        
classical          0.01796 NaN     0.01796 0.01796 1        
build_hazard_stats 0.01101 NaN     0.01101 0.01101 1        
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

Data transfer
-------------
================== ======================================================================== ========
task               sent                                                                     received
read_source_models monitor=736 B converter=638 B fnames=362 B                               12.46 KB
split_filter       srcs=11.06 KB monitor=381 B srcfilter=253 B sample_factor=21 B seed=15 B 12.32 KB
classical          group=12.37 KB param=636 B monitor=345 B src_filter=220 B gsims=129 B    1016 B  
build_hazard_stats pgetter=3.74 KB monitor=354 B hstats=67 B                                515 B   
================== ======================================================================== ========

Slowest operations
------------------
======================== ========= ========= ======
operation                time_sec  memory_mb counts
======================== ========= ========= ======
total classical          0.01796   0.36719   1     
total read_source_models 0.01553   0.0       2     
updating source_info     0.01354   0.0       1     
total build_hazard_stats 0.01101   0.53906   1     
combine pmaps            0.00991   0.53906   1     
get_poes                 0.00618   0.0       15    
total split_filter       0.00540   0.0       1     
managing sources         0.00521   0.0       1     
make_contexts            0.00449   0.0       15    
saving probability maps  0.00281   0.0       1     
store source_info        0.00260   0.0       1     
iter_ruptures            0.00155   0.0       15    
saving statistics        8.743E-04 0.0       1     
compute mean             6.616E-04 0.0       1     
aggregate curves         3.052E-04 0.0       1     
======================== ========= ========= ======