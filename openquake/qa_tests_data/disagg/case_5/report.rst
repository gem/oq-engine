CGS2017 PSHA model (Colombia), EventBased PSHA - test -  v.1 - 2018/02/11
=========================================================================

============== ===================
checksum32     1,136,041,000      
date           2019-05-03T06:43:31
engine_version 3.5.0-git7a6d15e809
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
====== ========= ==== ===== ===== ============ ========= ========= =======
grp_id source_id code gidx1 gidx2 num_ruptures calc_time num_sites weight 
====== ========= ==== ===== ===== ============ ========= ========= =======
0      buc06pt05 N    0     76    7            0.00751   1.00000   7.00000
1      buc16pt75 N    76    316   8            0.00517   1.00000   8.00000
====== ========= ==== ===== ===== ============ ========= ========= =======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
N    0.01268   2     
==== ========= ======

Information about the tasks
---------------------------
====================== ======= ======= ======= ======= =======
operation-duration     mean    stddev  min     max     outputs
read_source_models     0.00648 0.00118 0.00565 0.00732 2      
classical_split_filter 0.01767 NaN     0.01767 0.01767 1      
build_hazard_stats     0.00426 NaN     0.00426 0.00426 1      
====================== ======= ======= ======= ======= =======

Data transfer
-------------
====================== ====================================================== ========
task                   sent                                                   received
read_source_models     converter=626 B fnames=212 B                           12.78 KB
classical_split_filter srcs=11.14 KB params=608 B srcfilter=218 B gsims=163 B 5.03 KB 
build_hazard_stats     pgetter=0 B individual_curves=0 B hstats=0 B N=0 B     515 B   
====================== ====================================================== ========

Slowest operations
------------------
============================ ========= ========= ======
operation                    time_sec  memory_mb counts
============================ ========= ========= ======
total classical_split_filter 0.01767   0.24609   1     
total read_source_models     0.01297   0.0       2     
get_poes                     0.00483   0.0       15    
filtering/splitting sources  0.00438   0.24609   1     
saving probability maps      0.00434   0.0       1     
total build_hazard_stats     0.00426   0.0       1     
aggregate curves             0.00414   0.0       1     
combine pmaps                0.00368   0.0       1     
managing sources             0.00339   0.0       1     
make_contexts                0.00334   0.0       15    
store source model           0.00326   0.0       2     
store source_info            0.00240   0.0       1     
saving statistics            6.187E-04 0.0       1     
compute stats                3.550E-04 0.0       1     
============================ ========= ========= ======