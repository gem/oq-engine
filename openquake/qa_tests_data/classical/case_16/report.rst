Classical PSHA with non-trivial logic tree (1 source model + 5 (a, b) pairs per source + 3 Mmax per source
==========================================================================================================

============== ===================
checksum32     882_043_804        
date           2020-03-13T11:22:13
engine_version 3.9.0-gitfb3ef3a732
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
============================================= ======= ================
smlt_path                                     weight  num_realizations
============================================= ======= ================
b11_b21_b32_b41_b52_b61_b72_b81_b92_b101_b112 0.10000 1               
b11_b22_b32_b42_b52_b62_b72_b82_b92_b102_b112 0.40000 4               
b11_b23_b32_b43_b52_b63_b72_b83_b92_b103_b112 0.10000 1               
b11_b23_b33_b43_b53_b63_b73_b83_b93_b103_b113 0.30000 3               
b11_b24_b33_b44_b53_b64_b73_b84_b93_b104_b113 0.10000 1               
============================================= ======= ================

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
3         3      A    510          0.00693   0.05882   510         
2         2      A    450          0.00687   0.06667   450         
3         1      A    450          0.00665   0.06667   450         
3         4      A    510          0.00651   0.05882   510         
3         2      A    450          0.00649   0.06667   450         
4         1      A    375          0.00638   0.06667   375         
4         0      A    375          0.00607   0.06667   375         
5         4      A    425          0.00562   0.05882   425         
5         3      A    425          0.00547   0.05882   425         
4         4      A    425          0.00527   0.05882   425         
2         0      A    450          0.00511   0.06667   450         
5         0      A    375          0.00494   0.06667   375         
2         1      A    450          0.00486   0.06667   450         
2         3      A    510          0.00471   0.05882   510         
1         2      A    375          0.00452   0.06667   375         
4         3      A    425          0.00440   0.05882   425         
1         0      A    375          0.00439   0.06667   375         
3         0      A    450          0.00439   0.06667   450         
4         2      A    375          0.00432   0.06667   375         
2         4      A    510          0.00430   0.05882   510         
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
A    0.12861  
==== =========

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
preclassical       0.01494 0.00278 0.01006 0.01891 25     
read_source_model  0.02832 NaN     0.02832 0.02832 1      
================== ======= ======= ======= ======= =======

Data transfer
-------------
================= =============================================== ========
task              sent                                            received
read_source_model                                                 5.23 KB 
preclassical      srcs=49.11 KB params=15.58 KB srcfilter=5.44 KB 9.03 KB 
================= =============================================== ========

Slowest operations
------------------
=========================== ======== ========= ======
calc_66988                  time_sec memory_mb counts
=========================== ======== ========= ======
total preclassical          0.37360  0.94531   25    
splitting/filtering sources 0.22293  0.45703   25    
composite source model      0.15230  0.0       1     
total read_source_model     0.02832  0.0       1     
aggregate curves            0.00588  0.0       25    
store source_info           0.00258  0.0       1     
=========================== ======== ========= ======