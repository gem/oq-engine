Event Based QA Test, Case 1
===========================

============== ===================
checksum32     4_095_491_784      
date           2020-03-13T11:21:37
engine_version 3.9.0-gitfb3ef3a732
============== ===================

num_sites = 1, num_levels = 46, num_rlzs = 1

Parameters
----------
=============================== ==================
calculation_mode                'preclassical'    
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              50.0              
ses_per_logic_tree_path         2000              
truncation_level                2.0               
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                1.0               
area_source_discretization      20.0              
pointsource_distance            {'default': {}}   
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     42                
master_seed                     0                 
ses_seed                        1066              
=============================== ==================

Input files
-----------
======================= ========================
Name                    File                    
======================= ========================
gsim_logic_tree         `gmmLT.xml <gmmLT.xml>`_
job_ini                 `job.ini <job.ini>`_    
source_model_logic_tree `ssmLT.xml <ssmLT.xml>`_
======================= ========================

Composite source model
----------------------
========= ======= ================
smlt_path weight  num_realizations
========= ======= ================
b1        1.00000 1               
========= ======= ================

Required parameters per tectonic region type
--------------------------------------------
====== ========================== ========= ========== ==============
grp_id gsims                      distances siteparams ruptparams    
====== ========================== ========= ========== ==============
0      '[SiMidorikawa1999SInter]' rrup      vs30       hypo_depth mag
====== ========================== ========= ========== ==============

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      1.00000   10           10          
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
case_01   0      N    1            0.00178   1.00000   1.00000     
case_02   0      N    1            1.376E-04 1.00000   1.00000     
case_03   0      N    1            1.252E-04 1.00000   1.00000     
case_08   0      N    1            1.199E-04 1.00000   1.00000     
case_04   0      N    1            1.199E-04 1.00000   1.00000     
case_06   0      N    1            1.192E-04 1.00000   1.00000     
case_07   0      N    1            1.190E-04 1.00000   1.00000     
case_10   0      N    1            1.180E-04 1.00000   1.00000     
case_05   0      N    1            1.180E-04 1.00000   1.00000     
case_09   0      N    1            1.171E-04 1.00000   1.00000     
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
N    0.00288  
==== =========

Information about the tasks
---------------------------
================== ======= ====== ======= ======= =======
operation-duration mean    stddev min     max     outputs
preclassical       0.00373 NaN    0.00373 0.00373 1      
read_source_model  0.14162 NaN    0.14162 0.14162 1      
================== ======= ====== ======= ======= =======

Data transfer
-------------
================= =========================================== =========
task              sent                                        received 
read_source_model                                             755.96 KB
preclassical      srcs=774.52 KB params=986 B srcfilter=223 B 721 B    
================= =========================================== =========

Slowest operations
------------------
=========================== ========= ========= ======
calc_66949                  time_sec  memory_mb counts
=========================== ========= ========= ======
composite source model      0.38204   1.07422   1     
total read_source_model     0.14162   0.62500   1     
total preclassical          0.00373   1.60547   1     
store source_info           0.00220   0.0       1     
aggregate curves            4.585E-04 0.0       1     
splitting/filtering sources 2.046E-04 0.0       1     
=========================== ========= ========= ======