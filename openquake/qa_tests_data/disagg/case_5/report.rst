CGS2017 PSHA model (Colombia), EventBased PSHA - test -  v.1 - 2018/02/11
=========================================================================

============== ===================
checksum32     1_136_041_000      
date           2020-03-13T11:20:20
engine_version 3.9.0-gitfb3ef3a732
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
pointsource_distance            {'default': {}}   
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
========= ======= ================
smlt_path weight  num_realizations
========= ======= ================
b1        1.00000 1               
========= ======= ================

Required parameters per tectonic region type
--------------------------------------------
====== ========================= ========= ============ ==============
grp_id gsims                     distances siteparams   ruptparams    
====== ========================= ========= ============ ==============
0      '[MontalvaEtAl2017SSlab]' rhypo     backarc vs30 hypo_depth mag
====== ========================= ========= ============ ==============

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      1.00000   15           15          
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
buc16pt75 0      N    8            0.00260   1.00000   8.00000     
buc06pt05 0      N    7            0.00233   1.00000   7.00000     
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
N    0.00493  
==== =========

Information about the tasks
---------------------------
================== ======= ========= ======= ======= =======
operation-duration mean    stddev    min     max     outputs
preclassical       0.00326 1.893E-04 0.00313 0.00340 2      
read_source_model  0.00337 5.911E-04 0.00295 0.00379 2      
================== ======= ========= ======= ======= =======

Data transfer
-------------
================= ========================================== ========
task              sent                                       received
read_source_model converter=664 B fname=192 B srcfilter=8 B  12.57 KB
preclassical      srcs=16.4 KB params=1.5 KB srcfilter=446 B 728 B   
================= ========================================== ========

Slowest operations
------------------
=========================== ========= ========= ======
calc_66891                  time_sec  memory_mb counts
=========================== ========= ========= ======
composite source model      0.45893   0.0       1     
total read_source_model     0.00674   0.26953   2     
total preclassical          0.00653   1.34375   2     
store source_info           0.00216   0.0       1     
aggregate curves            6.020E-04 0.0       2     
splitting/filtering sources 5.059E-04 0.0       2     
=========================== ========= ========= ======