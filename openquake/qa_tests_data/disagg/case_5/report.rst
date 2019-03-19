CGS2017 PSHA model (Colombia), EventBased PSHA - test -  v.1 - 2018/02/11
=========================================================================

============== ===================
checksum32     1,136,041,000      
date           2019-03-19T10:03:22
engine_version 3.5.0-gitad6b69ea66
============== ===================

num_sites = 1, num_levels = 19, num_rlzs = 1

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
source_model_logic_tree `source_model_lt_col18_full_model_S_test_slab.xml <source_model_lt_col18_full_model_S_test_slab.xml>`_
======================= ======================================================================================================

Composite source model
----------------------
========= ======= ================ ================
smlt_path weight  gsim_logic_tree  num_realizations
========= ======= ================ ================
b1        1.00000 trivial(0,1,0,0) 1               
========= ======= ================ ================

Required parameters per tectonic region type
--------------------------------------------
====== ========================= ========== ============ ==============
grp_id gsims                     distances  siteparams   ruptparams    
====== ========================= ========== ============ ==============
0      '[MontalvaEtAl2017SSlab]' rhypo rrup backarc vs30 hypo_depth mag
1      '[MontalvaEtAl2017SSlab]' rhypo rrup backarc vs30 hypo_depth mag
====== ========================= ========== ============ ==============

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=2, rlzs=1)
  0,'[MontalvaEtAl2017SSlab]': [0]
  1,'[MontalvaEtAl2017SSlab]': [0]>

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
1      buc16pt75 N    76    316   8            0.00464   7.591E-04  8.00000   8         8.00000
0      buc06pt05 N    0     76    7            0.00436   2.086E-04  7.00000   7         7.00000
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= =======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
N    0.00900   2     
==== ========= ======

Information about the tasks
---------------------------
================== ======= ========= ======= ======= =======
operation-duration mean    stddev    min     max     outputs
read_source_models 0.00290 7.118E-04 0.00240 0.00340 2      
split_filter       0.00431 NaN       0.00431 0.00431 1      
classical          0.01155 NaN       0.01155 0.01155 1      
build_hazard_stats 0.00500 NaN       0.00500 0.00500 1      
================== ======= ========= ======= ======= =======

Fastest task
------------
taskno=0, weight=15, duration=0 s, sources="buc06pt05 buc16pt75"

======== ======= ====== ======= ======= ==
variable mean    stddev min     max     n 
======== ======= ====== ======= ======= ==
nsites   1.00000 0.0    1       1       15
weight   1.00000 0.0    1.00000 1.00000 15
======== ======= ====== ======= ======= ==

Slowest task
------------
taskno=0, weight=15, duration=0 s, sources="buc06pt05 buc16pt75"

======== ======= ====== ======= ======= ==
variable mean    stddev min     max     n 
======== ======= ====== ======= ======= ==
nsites   1.00000 0.0    1       1       15
weight   1.00000 0.0    1.00000 1.00000 15
======== ======= ====== ======= ======= ==

Data transfer
-------------
================== ========================================================= ========
task               sent                                                      received
read_source_models converter=626 B fnames=212 B                              12.78 KB
split_filter       srcs=11.14 KB srcfilter=253 B dummy=14 B                  12.37 KB
classical          group=12.42 KB param=594 B src_filter=220 B gsims=163 B   5.03 KB 
build_hazard_stats pgetter=3.99 KB hstats=65 B N=14 B individual_curves=13 B 515 B   
================== ========================================================= ========

Slowest operations
------------------
======================== ========= ========= ======
operation                time_sec  memory_mb counts
======================== ========= ========= ======
total classical          0.01155   1.57812   1     
aggregate curves         0.00603   0.0       1     
total read_source_models 0.00580   0.06641   2     
total build_hazard_stats 0.00500   1.31250   1     
combine pmaps            0.00434   1.30859   1     
saving probability maps  0.00434   0.0       1     
total split_filter       0.00431   1.52734   1     
store source model       0.00425   0.0       2     
managing sources         0.00412   0.01172   1     
get_poes                 0.00312   0.0       15    
make_contexts            0.00224   0.0       15    
store source_info        0.00198   0.0       1     
saving statistics        9.201E-04 0.0       1     
compute stats            3.150E-04 0.00391   1     
======================== ========= ========= ======