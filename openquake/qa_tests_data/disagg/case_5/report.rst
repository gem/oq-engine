CGS2017 PSHA model (Colombia), EventBased PSHA - test -  v.1 - 2018/02/11
=========================================================================

============== ===================
checksum32     1,136,041,000      
date           2019-06-24T15:33:26
engine_version 3.6.0-git4b6205639c
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

  <RlzsAssoc(size=2, rlzs=1)>

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
====== ========= ==== ===== ===== ============ ========= ========= ======= =============
grp_id source_id code gidx1 gidx2 num_ruptures calc_time num_sites weight  checksum     
====== ========= ==== ===== ===== ============ ========= ========= ======= =============
0      buc06pt05 N    0     76    7            0.00887   1.00000   7.00000 3,887,277,747
1      buc16pt75 N    76    316   8            0.00619   1.00000   8.00000 2,035,385,483
====== ========= ==== ===== ===== ============ ========= ========= ======= =============

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
N    0.01506   2     
==== ========= ======

Information about the tasks
---------------------------
====================== ======= ======= ======= ======= =======
operation-duration     mean    stddev  min     max     outputs
build_hazard_stats     0.00368 NaN     0.00368 0.00368 1      
classical_split_filter 0.02340 NaN     0.02340 0.02340 1      
read_source_models     0.00593 0.00178 0.00467 0.00720 2      
====================== ======= ======= ======= ======= =======

Data transfer
-------------
====================== ====================================================== ========
task                   sent                                                   received
build_hazard_stats     pgetter=0 B individual_curves=0 B hstats=0 B N=0 B     531 B   
classical_split_filter srcs=11.16 KB params=608 B srcfilter=220 B gsims=163 B 5.06 KB 
read_source_models     converter=626 B fnames=212 B                           12.79 KB
====================== ====================================================== ========

Slowest operations
------------------
============================ ========= ========= ======
operation                    time_sec  memory_mb counts
============================ ========= ========= ======
total classical_split_filter 0.02340   0.0       1     
total read_source_models     0.01187   0.0       2     
filtering/splitting sources  0.00705   0.0       1     
get_poes                     0.00507   0.0       15    
saving probability maps      0.00452   0.0       1     
total build_hazard_stats     0.00368   0.33594   1     
make_contexts                0.00361   0.0       15    
store source model           0.00360   0.0       2     
managing sources             0.00344   0.0       1     
aggregate curves             0.00333   0.0       1     
read PoEs                    0.00330   0.33594   1     
store source_info            0.00153   0.0       1     
saving statistics            5.426E-04 0.0       1     
compute stats                8.845E-05 0.0       1     
combine pmaps                6.056E-05 0.0       1     
============================ ========= ========= ======