Event Based Risk Lisbon
=======================

============== ===================
checksum32     1,182,973,928      
date           2019-10-01T06:32:35
engine_version 3.8.0-git66affb82eb
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
0         0      A    6,075        0.06349   1.00000   2.00000      31   
2         0      A    4,901        0.05716   1.00000   2.00000      34   
0         2      A    6,075        0.05258   1.00000   2.00000      38   
2         2      A    4,901        0.05157   1.00000   2.00000      38   
10        3      A    1,116        0.03007   1.00000   2.00000      66   
10        1      A    1,116        0.02752   1.00000   0.0          0.0  
4         1      A    310          0.01814   1.00000   0.0          0.0  
1         0      A    989          0.01753   1.00000   2.00000      114  
7         1      A    429          0.01528   1.00000   2.00000      130  
9         1      A    612          0.01484   1.00000   2.00000      134  
9         3      A    612          0.01420   1.00000   0.0          0.0  
4         3      A    310          0.01414   1.00000   0.0          0.0  
1         2      A    989          0.01254   1.00000   2.00000      159  
6         3      A    1,054        0.01221   1.00000   2.00000      163  
6         1      A    1,054        0.01191   1.00000   0.0          0.0  
5         3      A    551          0.01004   1.00000   2.00000      199  
5         1      A    551          0.00948   1.00000   0.0          0.0  
3         1      A    812          0.00883   1.00000   2.00000      226  
7         3      A    429          0.00860   1.00000   0.0          0.0  
3         3      A    812          0.00828   1.00000   0.0          0.0  
========= ====== ==== ============ ========= ========= ============ =====

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
A    0.47199   22    
==== ========= ======

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
SourceReader       0.17356 0.00800 0.16791 0.17922 2      
sample_ruptures    0.04183 0.01545 0.01433 0.06634 12     
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
calc_6460                time_sec  memory_mb counts
======================== ========= ========= ======
total sample_ruptures    0.50194   0.85156   12    
total SourceReader       0.34713   0.0       2     
EventBasedCalculator.run 0.34544   0.20703   1     
composite source model   0.19667   0.0       1     
saving ruptures          0.02050   0.0       10    
saving events            0.01118   0.20703   1     
store source_info        0.00247   0.0       1     
reading exposure         4.847E-04 0.0       1     
======================== ========= ========= ======