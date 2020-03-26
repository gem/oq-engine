Event Based QA Test, Case 12
============================

============== ===================
checksum32     3_308_955_350      
date           2020-03-13T11:21:38
engine_version 3.9.0-gitfb3ef3a732
============== ===================

num_sites = 1, num_levels = 3, num_rlzs = 1

Parameters
----------
=============================== ==================
calculation_mode                'preclassical'    
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              1.0               
ses_per_logic_tree_path         3500              
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
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gsim_logic_tree.xml <gsim_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

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
0      '[SadighEtAl1997]'    rrup      vs30       mag rake  
1      '[BooreAtkinson2008]' rjb       vs30       mag rake  
====== ===================== ========= ========== ==========

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      1.00000   1            1.00000     
1      1.00000   1            1.00000     
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
2         1      P    1            0.00186   1.00000   1.00000     
1         0      P    1            0.00161   1.00000   1.00000     
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
P    0.00348  
==== =========

Information about the tasks
---------------------------
================== ======= ========= ======= ======= =======
operation-duration mean    stddev    min     max     outputs
preclassical       0.00243 1.996E-04 0.00229 0.00257 2      
read_source_model  0.00120 NaN       0.00120 0.00120 1      
================== ======= ========= ======= ======= =======

Data transfer
-------------
================= =========================================== ========
task              sent                                        received
read_source_model                                             1.87 KB 
preclassical      srcs=2.23 KB params=1.25 KB srcfilter=446 B 736 B   
================= =========================================== ========

Slowest operations
------------------
=========================== ========= ========= ======
calc_66950                  time_sec  memory_mb counts
=========================== ========= ========= ======
composite source model      0.00912   0.0       1     
total preclassical          0.00486   1.45312   2     
store source_info           0.00227   0.0       1     
total read_source_model     0.00120   0.0       1     
aggregate curves            6.053E-04 0.0       2     
splitting/filtering sources 4.096E-04 0.0       2     
=========================== ========= ========= ======