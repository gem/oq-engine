applyToSources with multiple sources
====================================

============== ===================
checksum32     3,235,130,248      
date           2019-09-24T15:21:19
engine_version 3.7.0-git749bb363b3
============== ===================

num_sites = 1, num_levels = 1, num_rlzs = 9

Parameters
----------
=============================== ===================================================================================================================
calculation_mode                'preclassical'                                                                                                     
number_of_logic_tree_samples    9                                                                                                                  
maximum_distance                {'default': 30.0, 'Active Shallow Crust': 30.0, 'Subduction Interface': 100.0, 'Stable Continental Interior': 30.0}
investigation_time              1.0                                                                                                                
ses_per_logic_tree_path         1                                                                                                                  
truncation_level                None                                                                                                               
rupture_mesh_spacing            5.0                                                                                                                
complex_fault_mesh_spacing      50.0                                                                                                               
width_of_mfd_bin                0.5                                                                                                                
area_source_discretization      50.0                                                                                                               
ground_motion_correlation_model None                                                                                                               
minimum_intensity               {}                                                                                                                 
random_seed                     42                                                                                                                 
master_seed                     0                                                                                                                  
ses_seed                        42                                                                                                                 
=============================== ===================================================================================================================

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
=============================================== ======= =============== ================
smlt_path                                       weight  gsim_logic_tree num_realizations
=============================================== ======= =============== ================
b1_b211_b221_b231_b311_b321_b331_b341_b351_b361 0.11111 trivial(0,0,1)  1               
b1_b212_b222_b232_b312_b322_b332_b342_b352_b362 0.11111 trivial(0,0,1)  1               
b1_b213_b223_b233_b313_b323_b333_b343_b353_b363 0.11111 trivial(0,0,1)  1               
=============================================== ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================== ========= ========== ==========
grp_id gsims              distances siteparams ruptparams
====== ================== ========= ========== ==========
0      '[SadighEtAl1997]' rrup      vs30       mag rake  
1      '[SadighEtAl1997]' rrup      vs30       mag rake  
2      '[SadighEtAl1997]' rrup      vs30       mag rake  
3      '[SadighEtAl1997]' rrup      vs30       mag rake  
4      '[SadighEtAl1997]' rrup      vs30       mag rake  
5      '[SadighEtAl1997]' rrup      vs30       mag rake  
6      '[SadighEtAl1997]' rrup      vs30       mag rake  
7      '[SadighEtAl1997]' rrup      vs30       mag rake  
8      '[SadighEtAl1997]' rrup      vs30       mag rake  
====== ================== ========= ========== ==========

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=3, rlzs=9)>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== ============ ============
source_model     grp_id trt                  eff_ruptures tot_ruptures
================ ====== ==================== ============ ============
source_model.xml 1      Subduction Interface 633          633         
source_model.xml 4      Subduction Interface 656          633         
source_model.xml 7      Subduction Interface 633          633         
================ ====== ==================== ============ ============

============= ======
#TRT models   3     
#eff_ruptures 1,922 
#tot_ruptures 24,093
============= ======

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============ =======
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures speed  
========= ====== ==== ============ ========= ========= ============ =======
1         1      C    633          0.01873   3.00000   1,922        102,603
========= ====== ==== ============ ========= ========= ============ =======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
A    0.0       21    
C    0.01873   3     
S    0.0       9     
==== ========= ======

Information about the tasks
---------------------------
================== ======= ======= ========= ======= =======
operation-duration mean    stddev  min       max     outputs
preclassical       0.00442 0.00286 6.230E-04 0.00818 18     
read_source_models 0.26301 0.01084 0.25183   0.27348 3      
================== ======= ======= ========= ======= =======

Data transfer
-------------
================== =============================================== ========
task               sent                                            received
preclassical       srcs=57.26 KB srcfilter=13.2 KB params=10.49 KB 5.28 KB 
read_source_models converter=942 B fnames=321 B                    47.81 KB
================== =============================================== ========

Slowest operations
------------------
======================== ========= ========= ======
calc_1832                time_sec  memory_mb counts
======================== ========= ========= ======
total read_source_models 0.78904   0.41797   3     
total preclassical       0.07959   0.0       18    
aggregate curves         0.00397   0.0       18    
store source_info        0.00208   0.0       1     
managing sources         4.873E-04 0.0       1     
======================== ========= ========= ======