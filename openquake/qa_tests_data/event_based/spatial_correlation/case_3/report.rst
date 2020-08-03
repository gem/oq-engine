Probabilistic Event-Based QA Test with No Spatial Correlation, case 3
=====================================================================

============== ===================
checksum32     1_038_141_016      
date           2020-03-13T11:21:23
engine_version 3.9.0-gitfb3ef3a732
============== ===================

num_sites = 2, num_levels = 1, num_rlzs = 1

Parameters
----------
=============================== ==================
calculation_mode                'preclassical'    
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              50.0              
ses_per_logic_tree_path         300               
truncation_level                None              
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                0.1               
area_source_discretization      20.0              
pointsource_distance            {'default': {}}   
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     42                
master_seed                     0                 
ses_seed                        123456789         
=============================== ==================

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
0      2.00000   1            1.00000     
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
1         0      P    1            0.00163   2.00000   1.00000     
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
P    0.00163  
==== =========

Information about the tasks
---------------------------
================== ========= ====== ========= ========= =======
operation-duration mean      stddev min       max       outputs
preclassical       0.00225   NaN    0.00225   0.00225   1      
read_source_model  8.664E-04 NaN    8.664E-04 8.664E-04 1      
================== ========= ====== ========= ========= =======

Data transfer
-------------
================= ========================================= ========
task              sent                                      received
read_source_model                                           1.45 KB 
preclassical      srcs=1.11 KB params=612 B srcfilter=223 B 369 B   
================= ========================================= ========

Slowest operations
------------------
=========================== ========= ========= ======
calc_66936                  time_sec  memory_mb counts
=========================== ========= ========= ======
composite source model      0.00829   0.0       1     
store source_info           0.00240   0.0       1     
total preclassical          0.00225   1.54688   1     
total read_source_model     8.664E-04 0.0       1     
aggregate curves            4.110E-04 0.0       1     
splitting/filtering sources 1.705E-04 0.0       1     
=========================== ========= ========= ======