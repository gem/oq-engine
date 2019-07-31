Event Based Risk Lisbon
=======================

============== ===================
checksum32     1,182,973,928      
date           2019-07-30T15:04:37
engine_version 3.7.0-git3b3dff46da
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

Number of ruptures per tectonic region type
-------------------------------------------
=================== ====== ==================== ============ ============
source_model        grp_id trt                  eff_ruptures tot_ruptures
=================== ====== ==================== ============ ============
SA_RA_CATAL1_00.xml 0      Active Shallow Crust 3            11,965      
SA_RA_CATAL1_00.xml 1      Stable Shallow Crust 8            5,226       
SA_RA_CATAL2_00.xml 2      Active Shallow Crust 3            11,965      
SA_RA_CATAL2_00.xml 3      Stable Shallow Crust 8            5,226       
=================== ====== ==================== ============ ============

============= ======
#TRT models   4     
#eff_ruptures 22    
#tot_ruptures 34,382
============= ======

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
========= ====== ==== ============ ========= ========= ======= =====
source_id grp_id code num_ruptures calc_time num_sites weight  speed
========= ====== ==== ============ ========= ========= ======= =====
2         0      A    4,901        0.20337   2.00000   4.00000 19   
0         0      A    6,075        0.17622   2.00000   4.00000 22   
10        1      A    1,116        0.13359   2.00000   2.00000 14   
1         0      A    989          0.06634   2.00000   4.00000 60   
4         1      A    310          0.05591   2.00000   0.0     0.0  
3         1      A    812          0.04822   2.00000   2.00000 41   
9         1      A    612          0.04347   2.00000   2.00000 46   
7         1      A    429          0.04277   2.00000   2.00000 46   
5         1      A    551          0.03697   2.00000   2.00000 54   
6         1      A    1,054        0.03595   2.00000   2.00000 55   
8         1      A    342          0.01887   2.00000   0.0     0.0  
========= ====== ==== ============ ========= ========= ======= =====

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
A    0.86168   22    
==== ========= ======

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
read_source_models 0.15879 0.00222 0.15722 0.16036 2      
sample_ruptures    0.07441 0.03006 0.02597 0.13345 12     
================== ======= ======= ======= ======= =======

Data transfer
-------------
================== ================================================= ========
task               sent                                              received
read_source_models converter=628 B fnames=218 B                      20.87 KB
sample_ruptures    param=46.93 KB sources=31.58 KB srcfilter=2.58 KB 13.21 KB
================== ================================================= ========

Slowest operations
------------------
======================== ========= ========= ======
calc_15566               time_sec  memory_mb counts
======================== ========= ========= ======
total sample_ruptures    0.89292   0.0       12    
EventBasedCalculator.run 0.60765   1.00000   1     
total read_source_models 0.31758   0.0       2     
saving ruptures          0.03279   0.0       10    
saving events            0.02248   0.25781   1     
store source_info        0.00471   0.0       1     
reading exposure         5.381E-04 0.0       1     
======================== ========= ========= ======