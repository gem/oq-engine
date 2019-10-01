test for POE_TOO_BIG
====================

============== ===================
checksum32     3,490,620,350      
date           2019-10-01T06:32:22
engine_version 3.8.0-git66affb82eb
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
========= ======= ================= ================
smlt_path weight  gsim_logic_tree   num_realizations
========= ======= ================= ================
complex   0.33000 simple(3,0,0,0,0) 3               
point     0.67000 simple(3,0,0,0,0) 3               
========= ======= ================= ================

Required parameters per tectonic region type
--------------------------------------------
====== ========================================================== ============== ========== ==========
grp_id gsims                                                      distances      siteparams ruptparams
====== ========================================================== ============== ========== ==========
0      '[BindiEtAl2011]' '[BindiEtAl2014Rhyp]' '[CauzziEtAl2014]' rhypo rjb rrup vs30       mag rake  
1      '[BindiEtAl2011]' '[BindiEtAl2014Rhyp]' '[CauzziEtAl2014]' rhypo rjb rrup vs30       mag rake  
====== ========================================================== ============== ========== ==========

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=18, rlzs=6)>

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      1.00000   2,308        2,308       
1      4.00000   624          624         
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============ =======
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures speed  
========= ====== ==== ============ ========= ========= ============ =======
f1        0      C    2,308        0.00255   1.00000   2,308        903,364
p1        1      P    156          0.00239   1.00000   156          65,320 
p3        1      P    156          0.00238   1.00000   156          65,484 
p4        1      P    156          0.00238   1.00000   156          65,674 
p2        1      P    156          0.00215   1.00000   156          72,460 
========= ====== ==== ============ ========= ========= ============ =======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
C    0.00255   1     
P    0.00930   4     
==== ========= ======

Information about the tasks
---------------------------
================== ======= ========= ======= ======= =======
operation-duration mean    stddev    min     max     outputs
SourceReader       0.06224 0.07759   0.00738 0.11711 2      
preclassical       0.00285 1.291E-04 0.00262 0.00294 5      
================== ======= ========= ======= ======= =======

Data transfer
-------------
============ =========================================== ========
task         sent                                        received
SourceReader apply_unc=2.43 KB ltmodel=406 B fname=224 B 14.17 KB
preclassical params=11.33 KB srcs=7.9 KB gsims=2.34 KB   1.67 KB 
============ =========================================== ========

Slowest operations
------------------
====================== ======== ========= ======
calc_6394              time_sec memory_mb counts
====================== ======== ========= ======
composite source model 0.13396  0.0       1     
total SourceReader     0.12448  0.23438   2     
total preclassical     0.01426  0.0       5     
store source_info      0.00223  0.0       1     
aggregate curves       0.00150  0.0       5     
====================== ======== ========= ======