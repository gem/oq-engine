applyToSources with multiple sources
====================================

============== ===================
checksum32     3_235_130_248      
date           2020-01-16T05:31:46
engine_version 3.8.0-git83c45f7244
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
pointsource_distance            {'default': 0}                                                                                                     
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

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      NaN       80           0.0         
1      0.01264   633          633         
2      NaN       7_318        0.0         
3      NaN       100          0.0         
4      0.01372   656          656         
5      NaN       7_545        0.0         
6      NaN       80           0.0         
7      0.01264   633          633         
8      NaN       7_107        0.0         
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
1         4      C    656          0.01197   0.01372   656         
1         1      C    633          0.01025   0.01264   633         
1         7      C    633          0.00986   0.01264   633         
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
A    0.0      
C    0.03208  
S    0.0      
==== =========

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
SourceReader       0.46927 0.02449 0.44325 0.49187 3      
preclassical       0.24616 0.43455 0.01725 1.14366 15     
================== ======= ======= ======= ======= =======

Data transfer
-------------
============ ================================================ ========
task         sent                                             received
SourceReader apply_unc=10.92 KB ltmodel=753 B fname=312 B     65.21 KB
preclassical params=112.53 KB srcs=55.23 KB srcfilter=23.1 KB 4.78 KB 
============ ================================================ ========

Slowest operations
------------------
=========================== ========= ========= ======
calc_43325                  time_sec  memory_mb counts
=========================== ========= ========= ======
total preclassical          3.69243   1.33984   15    
splitting/filtering sources 3.38230   1.33984   15    
total SourceReader          1.40782   0.73828   3     
composite source model      0.52910   0.0       1     
store source_info           0.00258   0.0       1     
aggregate curves            8.090E-04 0.0       3     
=========================== ========= ========= ======