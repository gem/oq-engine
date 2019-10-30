Event Based Risk Lisbon
=======================

============== ===================
checksum32     1,753,463,320      
date           2019-10-23T16:26:30
engine_version 3.8.0-git2e0d8e6795
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
0      0.50000   11,965       6.00000     
1      1.33333   5,226        6.00000     
2      0.50000   11,965       6.00000     
3      1.33333   5,226        6.00000     
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
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
2         0      A    4,901        0.16889   0.50000   2.00000     
2         2      A    4,901        0.15632   0.50000   2.00000     
0         0      A    6,075        0.12819   0.50000   2.00000     
0         2      A    6,075        0.12192   0.50000   2.00000     
10        3      A    1,116        0.04503   0.50000   2.00000     
9         1      A    612          0.03637   0.50000   2.00000     
3         1      A    812          0.03614   0.50000   2.00000     
5         3      A    551          0.03447   0.50000   2.00000     
6         3      A    1,054        0.03295   0.50000   2.00000     
1         2      A    989          0.02361   0.50000   2.00000     
1         0      A    989          0.01162   0.50000   2.00000     
7         1      A    429          0.00952   0.50000   2.00000     
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
A    1.02790  
==== =========

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
SourceReader       0.26848 0.02483 0.25092 0.28604 2      
sample_ruptures    0.08769 0.04900 0.01337 0.17133 12     
================== ======= ======= ======= ======= =======

Data transfer
-------------
=============== ================================================= ========
task            sent                                              received
SourceReader    apply_unc=2.5 KB ltmodel=380 B fname=226 B        40.13 KB
sample_ruptures param=47.34 KB sources=31.37 KB srcfilter=2.61 KB 13.41 KB
=============== ================================================= ========

Slowest operations
------------------
======================== ========= ========= ======
calc_44514               time_sec  memory_mb counts
======================== ========= ========= ======
total sample_ruptures    1.05232   0.77734   12    
EventBasedCalculator.run 0.57208   0.0       1     
total SourceReader       0.53696   0.0       2     
composite source model   0.31850   0.0       1     
saving ruptures          0.03322   0.0       10    
saving events            0.01013   0.0       1     
store source_info        0.00233   0.0       1     
reading exposure         5.479E-04 0.0       1     
======================== ========= ========= ======