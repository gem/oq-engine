NNParametric
============

============== ===================
checksum32     1_135_602_540      
date           2020-03-13T11:22:03
engine_version 3.9.0-gitfb3ef3a732
============== ===================

num_sites = 1, num_levels = 19, num_rlzs = 1

Parameters
----------
=============================== ==================
calculation_mode                'preclassical'    
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 500.0}
investigation_time              1.0               
ses_per_logic_tree_path         1                 
truncation_level                2.0               
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                0.1               
area_source_discretization      5.0               
pointsource_distance            {'default': {}}   
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     23                
master_seed                     0                 
ses_seed                        42                
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
====== ===================== ========= ========== ==========
grp_id gsims                 distances siteparams ruptparams
====== ===================== ========= ========== ==========
0      '[BooreAtkinson2008]' rjb       vs30       mag rake  
====== ===================== ========= ========== ==========

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      1.00000   1            1.00000     
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
test      0      N    1            0.00169   1.00000   1.00000     
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
N    0.00169  
==== =========

Information about the tasks
---------------------------
================== ======= ====== ======= ======= =======
operation-duration mean    stddev min     max     outputs
preclassical       0.00233 NaN    0.00233 0.00233 1      
read_source_model  0.00136 NaN    0.00136 0.00136 1      
================== ======= ====== ======= ======= =======

Data transfer
-------------
================= ========================================= ========
task              sent                                      received
read_source_model                                           2.21 KB 
preclassical      srcs=2.08 KB params=768 B srcfilter=223 B 369 B   
================= ========================================= ========

Slowest operations
------------------
=========================== ========= ========= ======
calc_66974                  time_sec  memory_mb counts
=========================== ========= ========= ======
composite source model      0.01018   0.0       1     
store source_info           0.00249   0.0       1     
total preclassical          0.00233   0.99609   1     
total read_source_model     0.00136   0.0       1     
aggregate curves            4.199E-04 0.0       1     
splitting/filtering sources 1.869E-04 0.0       1     
=========================== ========= ========= ======