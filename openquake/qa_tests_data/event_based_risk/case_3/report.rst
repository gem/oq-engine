Event Based Risk Lisbon
=======================

============== ===================
checksum32     871_545_274        
date           2020-03-13T11:21:58
engine_version 3.9.0-gitfb3ef3a732
============== ===================

num_sites = 1, num_levels = 1, num_rlzs = 8

Parameters
----------
=============================== ==================
calculation_mode                'preclassical'    
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 400.0}
investigation_time              5.0               
ses_per_logic_tree_path         1                 
truncation_level                5.0               
rupture_mesh_spacing            4.0               
complex_fault_mesh_spacing      4.0               
width_of_mfd_bin                0.1               
area_source_discretization      20.0              
pointsource_distance            {'default': {}}   
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     23                
master_seed                     42                
ses_seed                        42                
=============================== ==================

Input files
-----------
======================== ============================================================
Name                     File                                                        
======================== ============================================================
exposure                 `exposure_model_1asset.xml <exposure_model_1asset.xml>`_    
gsim_logic_tree          `gsim_logic_tree.xml <gsim_logic_tree.xml>`_                
job_ini                  `job.ini <job.ini>`_                                        
source_model_logic_tree  `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
structural_vulnerability `vulnerability_model2013.xml <vulnerability_model2013.xml>`_
======================== ============================================================

Composite source model
----------------------
========= ======= ================
smlt_path weight  num_realizations
========= ======= ================
b1        0.60000 4               
b2        0.40000 4               
========= ======= ================

Required parameters per tectonic region type
--------------------------------------------
====== ========================================= ========= ========== ==========
grp_id gsims                                     distances siteparams ruptparams
====== ========================================= ========= ========== ==========
0      '[AkkarBommer2010]' '[AtkinsonBoore2006]' rjb rrup  vs30       mag rake  
1      '[AkkarBommer2010]' '[AtkinsonBoore2006]' rjb rrup  vs30       mag rake  
2      '[AkkarBommer2010]' '[AtkinsonBoore2006]' rjb rrup  vs30       mag rake  
3      '[AkkarBommer2010]' '[AtkinsonBoore2006]' rjb rrup  vs30       mag rake  
====== ========================================= ========= ========== ==========

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      0.02816   11_965       10_370      
1      0.02816   11_965       10_370      
2      0.05286   5_226        5_202       
3      0.05286   5_226        5_202       
====== ========= ============ ============

Exposure model
--------------
=========== =
#assets     1
#taxonomies 1
=========== =

======== ======= ====== === === ========= ==========
taxonomy mean    stddev min max num_sites num_assets
M1_2_PC  1.00000 NaN    1   1   1         1         
======== ======= ====== === === ========= ==========

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
0         0      A    6_075        0.01911   0.02222   6_075       
0         1      A    6_075        0.01880   0.02222   6_075       
2         0      A    4_901        0.01298   0.03448   3_306       
2         1      A    4_901        0.01163   0.03448   3_306       
10        3      A    1_116        0.00820   0.05556   1_116       
10        2      A    1_116        0.00778   0.05556   1_116       
1         0      A    989          0.00664   0.04348   989         
6         3      A    1_054        0.00574   0.03226   1_054       
9         3      A    612          0.00489   0.08333   588         
9         2      A    612          0.00477   0.08333   588         
3         3      A    812          0.00473   0.03448   812         
1         1      A    989          0.00460   0.04348   989         
6         2      A    1_054        0.00445   0.03226   1_054       
5         3      A    551          0.00388   0.03448   551         
8         2      A    342          0.00341   0.05556   342         
3         2      A    812          0.00333   0.03448   812         
7         2      A    429          0.00326   0.07692   429         
7         3      A    429          0.00326   0.07692   429         
4         2      A    310          0.00282   0.10000   310         
4         3      A    310          0.00274   0.10000   310         
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
A    0.14107  
==== =========

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
preclassical       0.04610 0.01254 0.02850 0.05783 11     
read_source_model  0.15439 0.01778 0.14182 0.16696 2      
================== ======= ======= ======= ======= =======

Data transfer
-------------
================= ========================================== ========
task              sent                                       received
read_source_model converter=664 B fname=212 B srcfilter=8 B  20.25 KB
preclassical      srcs=31.82 KB params=6.71 KB gsims=2.92 KB 4.43 KB 
================= ========================================== ========

Slowest operations
------------------
=========================== ========= ========= ======
calc_66967                  time_sec  memory_mb counts
=========================== ========= ========= ======
total preclassical          0.50714   2.07422   11    
splitting/filtering sources 0.33361   0.44141   11    
total read_source_model     0.30878   0.62109   2     
composite source model      0.24019   0.0       1     
store source_info           0.00223   0.0       1     
aggregate curves            0.00213   0.0       11    
reading exposure            5.739E-04 0.0       1     
=========================== ========= ========= ======