CGS2017 PSHA model (Colombia), EventBased PSHA - test -  v.1 - 2018/02/11
=========================================================================

============== ===================
checksum32     1_136_041_000      
date           2020-01-16T05:30:44
engine_version 3.8.0-git83c45f7244
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
pointsource_distance            None              
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
====== ========================= ========= ============ ==============
grp_id gsims                     distances siteparams   ruptparams    
====== ========================= ========= ============ ==============
0      '[MontalvaEtAl2017SSlab]' rhypo     backarc vs30 hypo_depth mag
1      '[MontalvaEtAl2017SSlab]' rhypo     backarc vs30 hypo_depth mag
====== ========================= ========= ============ ==============

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=2, rlzs=1)>

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      1.00000   7            7.00000     
1      1.00000   8            8.00000     
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
buc06pt05 0      N    7            0.00433   1.00000   7.00000     
buc16pt75 1      N    8            0.00254   1.00000   8.00000     
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
N    0.00686  
==== =========

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
SourceReader       0.01241 0.00649 0.00782 0.01700 2      
preclassical       0.00453 0.00170 0.00333 0.00573 2      
================== ======= ======= ======= ======= =======

Data transfer
-------------
============ ============================================ ========
task         sent                                         received
SourceReader apply_unc=2.27 KB ltmodel=420 B fname=206 B  18.53 KB
preclassical srcs=11.81 KB params=1.55 KB srcfilter=446 B 732 B   
============ ============================================ ========

Slowest operations
------------------
=========================== ========= ========= ======
calc_43224                  time_sec  memory_mb counts
=========================== ========= ========= ======
composite source model      0.03184   0.0       1     
total SourceReader          0.02481   0.0       2     
total preclassical          0.00906   0.0       2     
store source_info           0.00240   0.0       1     
splitting/filtering sources 6.342E-04 0.0       2     
aggregate curves            5.515E-04 0.0       2     
=========================== ========= ========= ======