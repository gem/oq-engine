Classical PSHA — using GMPE specrtal averaging
==============================================

============== ===================
checksum32     1_294_779_737      
date           2020-03-13T11:22:00
engine_version 3.9.0-gitfb3ef3a732
============== ===================

num_sites = 1, num_levels = 20, num_rlzs = 1

Parameters
----------
=============================== ==================
calculation_mode                'preclassical'    
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              50.0              
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                0.2               
area_source_discretization      10.0              
pointsource_distance            {'default': {}}   
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     23                
master_seed                     0                 
ses_seed                        42                
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
====== ================================================================================================================= ========= ========== ==========
grp_id gsims                                                                                                             distances siteparams ruptparams
====== ================================================================================================================= ========= ========== ==========
0      '[GenericGmpeAvgSA]\ngmpe_name = "BooreAtkinson2008"\navg_periods = [0.5, 1.0, 2.0]\ncorr_func = "baker_jayaram"' rjb       vs30       mag rake  
====== ================================================================================================================= ========= ========== ==========

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      0.07692   2_093        2_093       
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
956       0      A    2_093        0.01580   0.07692   2_093       
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
A    0.01580  
==== =========

Information about the tasks
---------------------------
================== ======= ====== ======= ======= =======
operation-duration mean    stddev min     max     outputs
preclassical       0.12450 NaN    0.12450 0.12450 1      
read_source_model  0.09242 NaN    0.09242 0.09242 1      
================== ======= ====== ======= ======= =======

Data transfer
-------------
================= ===================================== ========
task              sent                                  received
read_source_model                                       2.76 KB 
preclassical      srcs=2.81 KB gsims=980 B params=778 B 370 B   
================= ===================================== ========

Slowest operations
------------------
=========================== ========= ========= ======
calc_66970                  time_sec  memory_mb counts
=========================== ========= ========= ======
total preclassical          0.12450   0.49609   1     
splitting/filtering sources 0.10667   0.0       1     
composite source model      0.10058   0.0       1     
total read_source_model     0.09242   0.0       1     
store source_info           0.00220   0.0       1     
aggregate curves            4.017E-04 0.0       1     
=========================== ========= ========= ======