CGS2017 PSHA model (Colombia), EventBased PSHA - test -  v.1 - 2018/02/11
=========================================================================

============== ===================
checksum32     1,136,041,000      
date           2019-09-24T15:20:59
engine_version 3.7.0-git749bb363b3
============== ===================

num_sites = 1, num_levels = 19, num_rlzs = 1

Parameters
----------
=============================== ==================
calculation_mode                'preclassical'    
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
slab_buc0/6.05.nrml slab_buc1/6.75.nrml 0      Deep Seismicity 15           7           
slab_buc0/6.05.nrml slab_buc1/6.75.nrml 1      Deep Seismicity 15           8           
======================================= ====== =============== ============ ============

============= ==
#TRT models   2 
#eff_ruptures 30
#tot_ruptures 15
============= ==

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============ ======
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures speed 
========= ====== ==== ============ ========= ========= ============ ======
buc06pt05 0      N    7            7.207E-04 1.00000   7.00000      9,712 
buc16pt75 1      N    8            6.220E-04 1.00000   8.00000      12,861
========= ====== ==== ============ ========= ========= ============ ======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
N    0.00134   2     
==== ========= ======

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
preclassical       0.00192 NaN     0.00192 0.00192 1      
read_source_models 0.00399 0.00132 0.00305 0.00492 2      
================== ======= ======= ======= ======= =======

Data transfer
-------------
================== ========================================== ========
task               sent                                       received
preclassical       srcs=11.17 KB srcfilter=666 B params=647 B 392 B   
read_source_models converter=628 B fnames=212 B               12.79 KB
================== ========================================== ========

Slowest operations
------------------
======================== ========= ========= ======
calc_1737                time_sec  memory_mb counts
======================== ========= ========= ======
total read_source_models 0.00798   0.28906   2     
store source_info        0.00240   0.0       1     
total preclassical       0.00192   0.0       1     
managing sources         3.664E-04 0.0       1     
aggregate curves         2.496E-04 0.0       1     
======================== ========= ========= ======