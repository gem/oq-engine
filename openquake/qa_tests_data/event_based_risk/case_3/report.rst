Event Based Risk Lisbon
=======================

============== ===================
checksum32     1,182,973,928      
date           2019-10-01T07:01:06
engine_version 3.8.0-gitbd71c2f960
============== ===================

num_sites = 1, num_levels = 40, num_rlzs = 8

Parameters
----------
=============================== ==================
calculation_mode                'event_based_risk'
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 400.0}
investigation_time              5.0               
ses_per_logic_tree_path         1                 
truncation_level                5.0               
rupture_mesh_spacing            4.0               
complex_fault_mesh_spacing      4.0               
width_of_mfd_bin                0.1               
area_source_discretization      20.0              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     23                
master_seed                     42                
ses_seed                        42                
avg_losses                      True              
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
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
b1        0.60000 complex(2,2)    4               
b2        0.40000 complex(2,2)    4               
========= ======= =============== ================

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

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=16, rlzs=8)>

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      3.00000   11,965       6.00000     
1      8.00000   5,226        6.00000     
2      3.00000   11,965       6.00000     
3      8.00000   5,226        6.00000     
====== ========= ============ ============

Estimated data transfer for the avglosses
-----------------------------------------
1 asset(s) x 8 realization(s) x 1 loss type(s) losses x 8 bytes x 16 tasks = 1 KB

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
========= ====== ==== ============ ========= ========= ============ =====
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures speed
========= ====== ==== ============ ========= ========= ============ =====
2         0      A    4,901        0.11475   1.00000   2.00000      17   
2         2      A    4,901        0.06913   1.00000   2.00000      28   
0         0      A    6,075        0.05770   1.00000   2.00000      34   
0         2      A    6,075        0.05531   1.00000   2.00000      36   
9         1      A    612          0.03156   1.00000   2.00000      63   
10        3      A    1,116        0.02975   1.00000   2.00000      67   
7         1      A    429          0.02514   1.00000   2.00000      79   
10        1      A    1,116        0.02222   1.00000   0.0          0.0  
1         0      A    989          0.01862   1.00000   2.00000      107  
4         1      A    310          0.01801   1.00000   0.0          0.0  
1         2      A    989          0.01544   1.00000   2.00000      129  
9         3      A    612          0.01468   1.00000   0.0          0.0  
4         3      A    310          0.01389   1.00000   0.0          0.0  
6         1      A    1,054        0.01348   1.00000   0.0          0.0  
6         3      A    1,054        0.01242   1.00000   2.00000      161  
5         1      A    551          0.01066   1.00000   0.0          0.0  
5         3      A    551          0.01007   1.00000   2.00000      198  
7         3      A    429          0.00872   1.00000   0.0          0.0  
3         3      A    812          0.00834   1.00000   0.0          0.0  
3         1      A    812          0.00796   1.00000   2.00000      251  
========= ====== ==== ============ ========= ========= ============ =====

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
A    0.57209   22    
==== ========= ======

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
SourceReader       0.17698 0.00274 0.17504 0.17892 2      
sample_ruptures    0.05017 0.02731 0.01863 0.11837 12     
================== ======= ======= ======= ======= =======

Data transfer
-------------
=============== ================================================ ========
task            sent                                             received
SourceReader    apply_unc=2.5 KB ltmodel=380 B fname=226 B       38.29 KB
sample_ruptures param=47.43 KB sources=31.37 KB srcfilter=2.6 KB 13.41 KB
=============== ================================================ ========

Slowest operations
------------------
======================== ========= ========= ======
calc_6615                time_sec  memory_mb counts
======================== ========= ========= ======
total sample_ruptures    0.60199   0.89453   12    
EventBasedCalculator.run 0.39004   0.23438   1     
total SourceReader       0.35396   0.0       2     
composite source model   0.20017   0.23438   1     
saving ruptures          0.02270   0.0       10    
saving events            0.01102   0.0       1     
store source_info        0.00251   0.0       1     
reading exposure         4.649E-04 0.0       1     
======================== ========= ========= ======