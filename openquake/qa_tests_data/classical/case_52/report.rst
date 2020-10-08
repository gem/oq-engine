late_weights sampling
=====================

============== ====================
checksum32     2_199_567_850       
date           2020-07-31T16:43:29 
engine_version 3.10.0-git684982d357
============== ====================

num_sites = 1, num_levels = 20, num_rlzs = 10

Parameters
----------
=============================== ======================================
calculation_mode                'preclassical'                        
number_of_logic_tree_samples    10                                    
maximum_distance                {'default': [(1, 200.0), (10, 200.0)]}
investigation_time              1.0                                   
ses_per_logic_tree_path         1                                     
truncation_level                2.0                                   
rupture_mesh_spacing            1.0                                   
complex_fault_mesh_spacing      1.0                                   
width_of_mfd_bin                1.0                                   
area_source_discretization      None                                  
pointsource_distance            None                                  
ground_motion_correlation_model None                                  
minimum_intensity               {}                                    
random_seed                     1066                                  
master_seed                     0                                     
ses_seed                        42                                    
=============================== ======================================

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
========= ====== ================
smlt_path weight num_realizations
========= ====== ================
b11       10     10              
========= ====== ================

Required parameters per tectonic region type
--------------------------------------------
====== ====================================== ========= ========== ==========
grp_id gsims                                  distances siteparams ruptparams
====== ====================================== ========= ========== ==========
0      '[AkkarBommer2010]' '[SadighEtAl1997]' rjb rrup  vs30       mag rake  
====== ====================================== ========= ========== ==========

Slowest sources
---------------
========= ==== ============ ========= ========= ============
source_id code multiplicity calc_time num_sites eff_ruptures
========= ==== ============ ========= ========= ============
1         P    1            0.00201   0.33333   3           
========= ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
P    0.00201  
==== =========

Information about the tasks
---------------------------
================== ======= ====== ======= ======= =======
operation-duration mean    stddev min     max     outputs
preclassical       0.00270 NaN    0.00270 0.00270 1      
read_source_model  0.00228 NaN    0.00228 0.00228 1      
================== ======= ====== ======= ======= =======

Data transfer
-------------
================= ========================================= ========
task              sent                                      received
read_source_model                                           1.55 KB 
preclassical      srcs=1.24 KB params=706 B srcfilter=367 B 380 B   
classical                                                   0 B     
================= ========================================= ========

Slowest operations
------------------
=========================== ========= ========= ======
calc_44271                  time_sec  memory_mb counts
=========================== ========= ========= ======
composite source model      0.08885   0.84766   1     
total preclassical          0.00270   1.35156   1     
total read_source_model     0.00228   0.02344   1     
store source_info           9.463E-04 0.0       1     
aggregate curves            6.750E-04 0.0       1     
splitting/filtering sources 1.864E-04 0.0       1     
=========================== ========= ========= ======