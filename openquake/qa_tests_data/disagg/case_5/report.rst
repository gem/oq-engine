CGS2017 PSHA model (Colombia), EventBased PSHA - test -  v.1 - 2018/02/11
=========================================================================

============== ====================
checksum32     3_758_596_620       
date           2020-11-02T08:40:55 
engine_version 3.11.0-gitd13380ddb1
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
====== ======================= ====
grp_id gsim                    rlzs
====== ======================= ====
0      [MontalvaEtAl2017SSlab] [0] 
====== ======================= ====

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
buc16pt75 N    4.375E-04 1         8           
buc06pt05 N    4.203E-04 1         7           
========= ==== ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
N    8.578E-04
==== =========

Information about the tasks
---------------------------
================== ====== ========= ====== ========= =========
operation-duration counts mean      stddev min       max      
preclassical       2      9.216E-04 0%     9.208E-04 9.224E-04
read_source_model  2      0.00322   16%    0.00268   0.00376  
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
calc_46527, maxmem=1.0 GB time_sec memory_mb counts
========================= ======== ========= ======
importing inputs          1.02810  0.07031   1     
composite source model    1.02375  0.07031   1     
total read_source_model   0.00644  0.16016   2     
total preclassical        0.00184  0.42188   2     
========================= ======== ========= ======