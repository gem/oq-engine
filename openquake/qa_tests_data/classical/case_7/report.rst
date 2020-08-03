Classical Hazard QA Test, Case 7
================================

============== ===================
checksum32     1_870_360_642      
date           2020-03-13T11:22:58
engine_version 3.9.0-gitfb3ef3a732
============== ===================

num_sites = 1, num_levels = 3, num_rlzs = 2

Parameters
----------
=============================== ==================
calculation_mode                'preclassical'    
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              1.0               
ses_per_logic_tree_path         1                 
truncation_level                0.0               
rupture_mesh_spacing            0.1               
complex_fault_mesh_spacing      0.1               
width_of_mfd_bin                1.0               
area_source_discretization      10.0              
pointsource_distance            {'default': {}}   
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     1066              
master_seed                     0                 
ses_seed                        42                
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
b1        0.70000 1               
b2        0.30000 1               
========= ======= ================

Required parameters per tectonic region type
--------------------------------------------
====== ================== ========= ========== ==========
grp_id gsims              distances siteparams ruptparams
====== ================== ========= ========== ==========
0      '[SadighEtAl1997]' rrup      vs30       mag rake  
1      '[SadighEtAl1997]' rrup      vs30       mag rake  
====== ================== ========= ========== ==========

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      0.01429   140          140         
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
1         0      S    91           0.00312   0.01099   91          
2         0      C    49           0.00280   0.02041   49          
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
C    0.00280  
S    0.00312  
==== =========

Information about the tasks
---------------------------
================== ======= ========= ======= ======= =======
operation-duration mean    stddev    min     max     outputs
preclassical       0.00367 2.353E-04 0.00350 0.00384 2      
read_source_model  0.07471 0.07416   0.02227 0.12715 2      
================== ======= ========= ======= ======= =======

Data transfer
-------------
================= ========================================== ========
task              sent                                       received
read_source_model converter=664 B fname=196 B srcfilter=8 B  3.46 KB 
preclassical      srcs=2.6 KB params=1.25 KB srcfilter=446 B 743 B   
================= ========================================== ========

Slowest operations
------------------
=========================== ========= ========= ======
calc_67003                  time_sec  memory_mb counts
=========================== ========= ========= ======
composite source model      0.56808   0.0       1     
total read_source_model     0.14942   1.25000   2     
total preclassical          0.00734   1.30859   2     
store source_info           0.00208   0.0       1     
aggregate curves            6.990E-04 0.0       2     
splitting/filtering sources 4.220E-04 0.0       2     
=========================== ========= ========= ======