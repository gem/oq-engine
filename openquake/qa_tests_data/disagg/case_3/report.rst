test for POE_TOO_BIG
====================

============== ===================
checksum32     3_490_620_350      
date           2020-03-13T11:20:26
engine_version 3.9.0-gitfb3ef3a732
============== ===================

num_sites = 1, num_levels = 200, num_rlzs = 6

Parameters
----------
=============================== ==============================================================================================================================================================
calculation_mode                'preclassical'                                                                                                                                                
number_of_logic_tree_samples    0                                                                                                                                                             
maximum_distance                {'default': 200.0, 'Stable Shallow Crust': 200.0, 'Active Shallow Crust': 200.0, 'Volcanic': 100.0, 'Subduction Interface': 200.0, 'Subduction Inslab': 200.0}
investigation_time              50.0                                                                                                                                                          
ses_per_logic_tree_path         1                                                                                                                                                             
truncation_level                3.0                                                                                                                                                           
rupture_mesh_spacing            5.0                                                                                                                                                           
complex_fault_mesh_spacing      5.0                                                                                                                                                           
width_of_mfd_bin                0.1                                                                                                                                                           
area_source_discretization      15.0                                                                                                                                                          
pointsource_distance            {'default': {}}                                                                                                                                               
ground_motion_correlation_model None                                                                                                                                                          
minimum_intensity               {}                                                                                                                                                            
random_seed                     23                                                                                                                                                            
master_seed                     0                                                                                                                                                             
ses_seed                        42                                                                                                                                                            
=============================== ==============================================================================================================================================================

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
complex   0.33000 3               
point     0.67000 3               
========= ======= ================

Required parameters per tectonic region type
--------------------------------------------
====== ========================================================== ============== ========== ==========
grp_id gsims                                                      distances      siteparams ruptparams
====== ========================================================== ============== ========== ==========
0      '[BindiEtAl2011]' '[BindiEtAl2014Rhyp]' '[CauzziEtAl2014]' rhypo rjb rrup vs30       mag rake  
1      '[BindiEtAl2011]' '[BindiEtAl2014Rhyp]' '[CauzziEtAl2014]' rhypo rjb rrup vs30       mag rake  
====== ========================================================== ============== ========== ==========

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      0.01603   2_308        2_308       
1      0.00641   624          624         
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
f1        0      C    2_308        0.12166   0.01603   2_308       
p1        1      P    156          0.00175   0.00641   156         
p4        1      P    156          1.240E-04 0.00641   156         
p2        1      P    156          9.966E-05 0.00641   156         
p3        1      P    156          8.941E-05 0.00641   156         
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
C    0.12166  
P    0.00206  
==== =========

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
preclassical       2.37597 3.35618 0.00280 4.74915 2      
read_source_model  0.04903 0.06511 0.00299 0.09508 2      
================== ======= ======= ======= ======= =======

Data transfer
-------------
================= ========================================= ========
task              sent                                      received
read_source_model converter=664 B fname=210 B srcfilter=8 B 5.92 KB 
preclassical      srcs=5.35 KB params=5.05 KB gsims=960 B   858 B   
================= ========================================= ========

Slowest operations
------------------
=========================== ========= ========= ======
calc_66895                  time_sec  memory_mb counts
=========================== ========= ========= ======
total preclassical          4.75195   5.98828   2     
splitting/filtering sources 4.62568   4.16016   2     
composite source model      0.50383   0.00391   1     
total read_source_model     0.09807   1.17969   2     
store source_info           0.00252   0.0       1     
aggregate curves            9.217E-04 0.0       2     
=========================== ========= ========= ======