Classical PSHA with non-trivial logic tree (1 source model + 5 (a, b) pairs per source + 3 Mmax per source
==========================================================================================================

============== ===================
checksum32     882_043_804        
date           2020-01-16T05:31:17
engine_version 3.8.0-git83c45f7244
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
pointsource_distance            None              
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
0      0.06667   2_025        2_025       
1      0.06667   2_025        2_025       
2      0.06667   2_025        2_025       
3      0.05882   2_295        2_295       
4      0.05882   2_295        2_295       
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
3         1      A    450          0.00688   0.06667   450         
3         4      A    510          0.00663   0.05882   510         
3         2      A    450          0.00657   0.06667   450         
2         0      A    450          0.00590   0.06667   450         
3         3      A    510          0.00550   0.05882   510         
3         0      A    450          0.00522   0.06667   450         
4         4      A    425          0.00513   0.05882   425         
5         3      A    425          0.00504   0.05882   425         
4         1      A    375          0.00502   0.06667   375         
2         4      A    510          0.00498   0.05882   510         
5         2      A    375          0.00498   0.06667   375         
5         1      A    375          0.00488   0.06667   375         
1         1      A    375          0.00487   0.06667   375         
4         2      A    375          0.00478   0.06667   375         
2         1      A    450          0.00469   0.06667   450         
5         4      A    425          0.00435   0.05882   425         
2         2      A    450          0.00435   0.06667   450         
2         3      A    510          0.00432   0.05882   510         
1         2      A    375          0.00430   0.06667   375         
1         3      A    425          0.00419   0.05882   425         
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
A    0.12210  
==== =========

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
SourceReader       0.05803 0.00160 0.05614 0.06028 5      
preclassical       0.01395 0.00208 0.00930 0.01673 25     
================== ======= ======= ======= ======= =======

Data transfer
-------------
============ =============================================== ========
task         sent                                            received
SourceReader apply_unc=21.92 KB ltmodel=1.23 KB fname=520 B  35.26 KB
preclassical srcs=48.43 KB params=16.19 KB srcfilter=5.44 KB 8.94 KB 
============ =============================================== ========

Slowest operations
------------------
=========================== ======== ========= ======
calc_43318                  time_sec memory_mb counts
=========================== ======== ========= ======
total preclassical          0.34877  0.0       25    
total SourceReader          0.29015  0.0       5     
splitting/filtering sources 0.20687  0.0       25    
composite source model      0.10782  0.0       1     
aggregate curves            0.00454  0.0       25    
store source_info           0.00260  0.0       1     
=========================== ======== ========= ======