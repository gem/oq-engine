Etna No Topo
============

============== ===================
checksum32     380_532_669        
date           2020-03-13T11:23:00
engine_version 3.9.0-gitfb3ef3a732
============== ===================

num_sites = 1, num_levels = 28, num_rlzs = 1

Parameters
----------
=============================== =================
calculation_mode                'preclassical'   
number_of_logic_tree_samples    0                
maximum_distance                {'default': 50.0}
investigation_time              50.0             
ses_per_logic_tree_path         1                
truncation_level                3.0              
rupture_mesh_spacing            1.0              
complex_fault_mesh_spacing      1.0              
width_of_mfd_bin                0.1              
area_source_discretization      1.0              
pointsource_distance            {'default': {}}  
ground_motion_correlation_model None             
minimum_intensity               {}               
random_seed                     23               
master_seed                     0                
ses_seed                        42               
=============================== =================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
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
====== ======================= ========= ========== ==========
grp_id gsims                   distances siteparams ruptparams
====== ======================= ========= ========== ==========
0      '[TusaLanger2016Rhypo]' rhypo     vs30       mag       
====== ======================= ========= ========== ==========

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      0.06000   150          150         
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
SVF       0      S    150          0.01443   0.06000   150         
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
S    0.01443  
==== =========

Information about the tasks
---------------------------
================== ======= ====== ======= ======= =======
operation-duration mean    stddev min     max     outputs
preclassical       0.01528 NaN    0.01528 0.01528 1      
read_source_model  0.00324 NaN    0.00324 0.00324 1      
================== ======= ====== ======= ======= =======

Data transfer
-------------
================= ========================================= ========
task              sent                                      received
read_source_model                                           1.7 KB  
preclassical      srcs=1.65 KB params=840 B srcfilter=223 B 357 B   
================= ========================================= ========

Slowest operations
------------------
=========================== ========= ========= ======
calc_67005                  time_sec  memory_mb counts
=========================== ========= ========= ======
total preclassical          0.01528   1.17188   1     
composite source model      0.01445   0.0       1     
total read_source_model     0.00324   0.0       1     
store source_info           0.00241   0.0       1     
aggregate curves            4.129E-04 0.0       1     
splitting/filtering sources 2.928E-04 0.0       1     
=========================== ========= ========= ======