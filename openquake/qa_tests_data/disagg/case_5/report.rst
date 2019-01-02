CGS2017 PSHA model (Colombia), EventBased PSHA - test -  v.1 - 2018/02/11
=========================================================================

============== ===================
checksum32     1,136,041,000      
date           2018-12-13T12:57:06
engine_version 3.3.0-git68d7d11268
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
0      MontalvaEtAl2017SSlab() rhypo rrup backarc vs30 hypo_depth mag
1      MontalvaEtAl2017SSlab() rhypo rrup backarc vs30 hypo_depth mag
====== ======================= ========== ============ ==============

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=2, rlzs=1)
  0,MontalvaEtAl2017SSlab(): [0]
  1,MontalvaEtAl2017SSlab(): [0]>

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
0      buc06pt05 N    0     76    7            0.00677   4.823E-04  7.00000   7         7.00000
1      buc16pt75 N    0     240   8            0.00909   3.242E-04  8.00000   8         8.00000
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= =======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
N    0.01586   2     
==== ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ========= ======= ======= =======
operation-duration mean    stddev    min     max     outputs
read_source_models 0.00597 6.684E-04 0.00550 0.00645 2      
split_filter       0.00652 NaN       0.00652 0.00652 1      
classical          0.00878 0.00177   0.00753 0.01003 2      
build_hazard_stats 0.00559 NaN       0.00559 0.00559 1      
================== ======= ========= ======= ======= =======

Fastest task
------------
taskno=2, weight=7, duration=0 s, sources="buc16pt75"

======== ======= ====== ======= ======= =
variable mean    stddev min     max     n
======== ======= ====== ======= ======= =
nsites   1.00000 0.0    1       1       8
weight   1.00000 0.0    1.00000 1.00000 8
======== ======= ====== ======= ======= =

Slowest task
------------
taskno=2, weight=8, duration=0 s, sources="buc16pt75"

======== ======= ====== ======= ======= =
variable mean    stddev min     max     n
======== ======= ====== ======= ======= =
nsites   1.00000 0.0    1       1       8
weight   1.00000 0.0    1.00000 1.00000 8
======== ======= ====== ======= ======= =

Data transfer
-------------
================== =========================================================== ========
task               sent                                                        received
read_source_models converter=776 B fnames=212 B                                12.45 KB
split_filter       srcs=11.08 KB srcfilter=253 B seed=14 B                     12.32 KB
classical          group=12.94 KB src_filter=1.59 KB param=1.16 KB gsims=258 B 1.43 KB 
build_hazard_stats pgetter=3.67 KB hstats=67 B                                 515 B   
================== =========================================================== ========

Slowest operations
------------------
======================== ========= ========= ======
operation                time_sec  memory_mb counts
======================== ========= ========= ======
total classical          0.01756   0.14844   2     
total read_source_models 0.01195   0.0       2     
get_poes                 0.00706   0.0       15    
total split_filter       0.00652   0.0       1     
total build_hazard_stats 0.00559   0.50391   1     
make_contexts            0.00514   0.0       15    
combine pmaps            0.00501   0.50391   1     
store source_info        0.00440   0.0       2     
managing sources         0.00327   0.0       1     
store source model       0.00245   0.0       2     
saving probability maps  0.00243   0.0       1     
iter_ruptures            0.00184   0.0       15    
saving statistics        9.692E-04 0.0       1     
aggregate curves         5.236E-04 0.0       2     
compute mean             3.493E-04 0.0       1     
======================== ========= ========= ======