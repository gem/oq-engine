Classical Hazard QA Test, Case 4
================================

============== ===================
checksum32     1_597_036_579      
date           2020-03-13T11:22:05
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
b1        1.00000 1               
========= ======= ================

Required parameters per tectonic region type
--------------------------------------------
====== ================== ========= ========== ==========
grp_id gsims              distances siteparams ruptparams
====== ================== ========= ========== ==========
0      '[SadighEtAl1997]' rrup      vs30       mag rake  
====== ================== ========= ========== ==========

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      0.01099   91           91          
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
1         0      S    91           0.00306   0.01099   91          
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
S    0.00306  
==== =========

Information about the tasks
---------------------------
================== ======= ====== ======= ======= =======
operation-duration mean    stddev min     max     outputs
preclassical       0.00370 NaN    0.00370 0.00370 1      
read_source_model  0.02205 NaN    0.02205 0.02205 1      
================== ======= ====== ======= ======= =======

Data transfer
-------------
================= ======================================== ========
task              sent                                     received
read_source_model                                          1.45 KB 
preclassical      srcs=1.3 KB params=638 B srcfilter=223 B 369 B   
================= ======================================== ========

Slowest operations
------------------
=========================== ========= ========= ======
calc_66980                  time_sec  memory_mb counts
=========================== ========= ========= ======
composite source model      0.03214   0.0       1     
total read_source_model     0.02205   0.0       1     
total preclassical          0.00370   1.79297   1     
store source_info           0.00243   0.0       1     
aggregate curves            3.841E-04 0.0       1     
splitting/filtering sources 1.910E-04 0.0       1     
=========================== ========= ========= ======