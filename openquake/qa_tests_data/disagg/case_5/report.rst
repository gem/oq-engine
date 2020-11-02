CGS2017 PSHA model (Colombia), EventBased PSHA - test -  v.1 - 2018/02/11
=========================================================================

============== ====================
checksum32     3_758_596_620       
date           2020-11-02T09:35:35 
engine_version 3.11.0-git82b78631ac
============== ====================

num_sites = 1, num_levels = 19, num_rlzs = 1

Parameters
----------
=============================== ==========================================
calculation_mode                'preclassical'                            
number_of_logic_tree_samples    0                                         
maximum_distance                {'default': [(1.0, 200.0), (10.0, 200.0)]}
investigation_time              1.0                                       
ses_per_logic_tree_path         1                                         
truncation_level                3.0                                       
rupture_mesh_spacing            2.0                                       
complex_fault_mesh_spacing      2.0                                       
width_of_mfd_bin                0.1                                       
area_source_discretization      5.0                                       
pointsource_distance            None                                      
ground_motion_correlation_model None                                      
minimum_intensity               {}                                        
random_seed                     1024                                      
master_seed                     0                                         
ses_seed                        42                                        
=============================== ==========================================

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
====== ========================= ====
grp_id gsim                      rlzs
====== ========================= ====
0      '[MontalvaEtAl2017SSlab]' [0] 
====== ========================= ====

Required parameters per tectonic region type
--------------------------------------------
===== ========================= ========= ============ ==============
et_id gsims                     distances siteparams   ruptparams    
===== ========================= ========= ============ ==============
0     '[MontalvaEtAl2017SSlab]' rhypo     backarc vs30 hypo_depth mag
===== ========================= ========= ============ ==============

Slowest sources
---------------
========= ==== ========= ========= ============
source_id code calc_time num_sites eff_ruptures
========= ==== ========= ========= ============
buc16pt75 N    4.685E-04 1         8           
buc06pt05 N    4.320E-04 1         7           
========= ==== ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
N    9.005E-04
==== =========

Information about the tasks
---------------------------
================== ====== ========= ====== ========= =========
operation-duration counts mean      stddev min       max      
preclassical       2      9.902E-04 0%     9.859E-04 9.944E-04
read_source_model  2      0.00333   16%    0.00277   0.00389  
================== ====== ========= ====== ========= =========

Data transfer
-------------
================= =============================== ========
task              sent                            received
read_source_model converter=664 B fname=192 B     12.54 KB
preclassical      srcs=12.12 KB srcfilter=1.74 KB 494 B   
================= =============================== ========

Slowest operations
------------------
========================= ======== ========= ======
calc_47241, maxmem=1.0 GB time_sec memory_mb counts
========================= ======== ========= ======
importing inputs          1.02944  0.01953   1     
composite source model    1.02439  0.01953   1     
total read_source_model   0.00666  0.51172   2     
total preclassical        0.00198  0.38281   2     
========================= ======== ========= ======