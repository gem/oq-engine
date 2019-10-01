Classical PSHA with non-trivial logic tree (1 source model + 5 (a, b) pairs per source + 3 Mmax per source
==========================================================================================================

============== ===================
checksum32     1,751,642,476      
date           2019-10-01T06:32:39
engine_version 3.8.0-git66affb82eb
============== ===================

num_sites = 1, num_levels = 3, num_rlzs = 10

Parameters
----------
=============================== ==================
calculation_mode                'preclassical'    
number_of_logic_tree_samples    10                
maximum_distance                {'default': 200.0}
investigation_time              50.0              
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                0.1               
area_source_discretization      10.0              
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
============================================= ======= =============== ================
smlt_path                                     weight  gsim_logic_tree num_realizations
============================================= ======= =============== ================
b11_b21_b32_b41_b52_b61_b72_b81_b92_b101_b112 0.10000 trivial(1)      1               
b11_b22_b32_b42_b52_b62_b72_b82_b92_b102_b112 0.10000 trivial(1)      1               
b11_b23_b32_b43_b52_b63_b72_b83_b92_b103_b112 0.10000 trivial(1)      1               
b11_b23_b33_b43_b53_b63_b73_b83_b93_b103_b113 0.10000 trivial(1)      1               
b11_b24_b33_b44_b53_b64_b73_b84_b93_b104_b113 0.10000 trivial(1)      1               
============================================= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ===================== ========= ========== ==========
grp_id gsims                 distances siteparams ruptparams
====== ===================== ========= ========== ==========
0      '[BooreAtkinson2008]' rjb       vs30       mag rake  
1      '[BooreAtkinson2008]' rjb       vs30       mag rake  
2      '[BooreAtkinson2008]' rjb       vs30       mag rake  
3      '[BooreAtkinson2008]' rjb       vs30       mag rake  
4      '[BooreAtkinson2008]' rjb       vs30       mag rake  
====== ===================== ========= ========== ==========

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=5, rlzs=10)>

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      5.00000   2,025        2,025       
1      5.00000   2,025        2,025       
2      5.00000   2,025        2,025       
3      5.00000   2,295        2,295       
4      5.00000   2,295        2,295       
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============ =======
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures speed  
========= ====== ==== ============ ========= ========= ============ =======
2         0      A    450          0.00252   1.00000   450          178,329
5         4      A    425          0.00226   1.00000   425          188,413
1         1      A    375          0.00221   1.00000   375          169,508
1         0      A    375          0.00220   1.00000   375          170,741
4         0      A    375          0.00219   1.00000   375          171,038
1         4      A    425          0.00205   1.00000   425          207,421
2         4      A    510          0.00203   1.00000   510          251,540
3         4      A    510          0.00196   1.00000   510          260,579
2         2      A    450          0.00192   1.00000   450          234,028
4         2      A    375          0.00183   1.00000   375          204,987
4         1      A    375          0.00172   1.00000   375          217,909
2         3      A    510          0.00169   1.00000   510          301,621
3         2      A    450          0.00169   1.00000   450          266,776
4         3      A    425          0.00164   1.00000   425          259,927
5         2      A    375          0.00163   1.00000   375          230,153
3         1      A    450          0.00161   1.00000   450          279,579
1         3      A    425          0.00157   1.00000   425          270,621
1         2      A    375          0.00157   1.00000   375          238,928
5         0      A    375          0.00156   1.00000   375          240,095
3         0      A    450          0.00155   1.00000   450          289,440
========= ====== ==== ============ ========= ========= ============ =======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
A    0.04426   25    
==== ========= ======

Information about the tasks
---------------------------
================== ======= ========= ======= ======= =======
operation-duration mean    stddev    min     max     outputs
SourceReader       0.05529 0.00308   0.05082 0.05873 5      
preclassical       0.00226 5.107E-04 0.00144 0.00387 25     
================== ======= ========= ======= ======= =======

Data transfer
-------------
============ =============================================== ========
task         sent                                            received
SourceReader apply_unc=21.92 KB ltmodel=1.23 KB fname=520 B  49.08 KB
preclassical srcs=48.02 KB params=12.65 KB srcfilter=5.42 KB 8.35 KB 
============ =============================================== ========

Slowest operations
------------------
====================== ======== ========= ======
calc_6479              time_sec memory_mb counts
====================== ======== ========= ======
total SourceReader     0.27644  0.0       5     
composite source model 0.10062  0.0       1     
total preclassical     0.05640  0.0       25    
aggregate curves       0.00666  0.0       25    
store source_info      0.00262  0.0       1     
====================== ======== ========= ======