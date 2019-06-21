Event Based Risk Lisbon
=======================

============== ===================
checksum32     1,182,973,928      
date           2019-06-21T09:42:30
engine_version 3.6.0-git17fd0581aa
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

  <RlzsAssoc(size=8, rlzs=8)
  0,'[AkkarBommer2010]': [2 3]
  0,'[AtkinsonBoore2006]': [0 1]
  1,'[AkkarBommer2010]': [1 3]
  1,'[AtkinsonBoore2006]': [0 2]
  2,'[AkkarBommer2010]': [6 7]
  2,'[AtkinsonBoore2006]': [4 5]
  3,'[AkkarBommer2010]': [5 7]
  3,'[AtkinsonBoore2006]': [4 6]>

Number of ruptures per tectonic region type
-------------------------------------------
=================== ====== ==================== ============ ============
source_model        grp_id trt                  eff_ruptures tot_ruptures
=================== ====== ==================== ============ ============
SA_RA_CATAL1_00.xml 0      Active Shallow Crust 11,965       11,965      
SA_RA_CATAL1_00.xml 1      Stable Shallow Crust 5,226        5,226       
SA_RA_CATAL2_00.xml 2      Active Shallow Crust 11,965       11,965      
SA_RA_CATAL2_00.xml 3      Stable Shallow Crust 5,226        5,226       
=================== ====== ==================== ============ ============

============= ======
#TRT models   4     
#eff_ruptures 34,382
#tot_ruptures 34,382
#tot_weight   34,382
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
====== ========= ==== ===== ===== ============ ========= ========= =======
grp_id source_id code gidx1 gidx2 num_ruptures calc_time num_sites weight 
====== ========= ==== ===== ===== ============ ========= ========= =======
0      0         A    0     4     6,075        0.05784   0.0       2.00000
2      0         A    44    48    6,075        0.05628   0.0       2.00000
0      2         A    8     12    4,901        0.05626   0.0       2.00000
2      2         A    52    56    4,901        0.04544   0.0       2.00000
1      4         A    20    24    310          0.03603   0.0       0.0    
3      10        A    56    60    1,116        0.02895   0.0       2.00000
1      10        A    12    16    1,116        0.02592   0.0       0.0    
0      1         A    4     8     989          0.01890   0.0       2.00000
3      9         A    84    88    612          0.01642   0.0       0.0    
3      4         A    64    68    310          0.01629   0.0       0.0    
2      1         A    48    52    989          0.01626   0.0       2.00000
1      9         A    40    44    612          0.01441   0.0       2.00000
3      6         A    72    76    1,054        0.01419   0.0       2.00000
1      6         A    28    32    1,054        0.01414   0.0       0.0    
1      7         A    32    36    429          0.01249   0.0       2.00000
3      5         A    68    72    551          0.01143   0.0       2.00000
1      5         A    24    28    551          0.01113   0.0       0.0    
1      3         A    16    20    812          0.00919   0.0       2.00000
3      7         A    76    80    429          0.00916   0.0       0.0    
3      3         A    60    64    812          0.00868   0.0       0.0    
====== ========= ==== ===== ===== ============ ========= ========= =======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
A    0.49378   22    
==== ========= ======

Duplicated sources
------------------
['0', '1', '10', '2', '3', '4', '5', '6', '7', '8', '9']
Found 11 source(s) with the same ID and 11 true duplicate(s)

Information about the tasks
---------------------------
================== ========= ========= ========= ======= =======
operation-duration mean      stddev    min       max     outputs
get_eid_rlz        7.591E-04 2.774E-04 4.191E-04 0.00124 11     
read_source_models 0.15748   0.03099   0.13557   0.17939 2      
sample_ruptures    0.04384   0.01479   0.01961   0.06443 12     
================== ========= ========= ========= ======= =======

Data transfer
-------------
================== ================================================ ========
task               sent                                             received
get_eid_rlz        self=18.58 KB                                    3.47 KB 
read_source_models converter=626 B fnames=232 B                     20.81 KB
sample_ruptures    param=47.43 KB sources=31.3 KB srcfilter=2.58 KB 13.08 KB
================== ================================================ ========

Slowest operations
------------------
======================== ========= ========= ======
operation                time_sec  memory_mb counts
======================== ========= ========= ======
total sample_ruptures    0.52607   0.86328   12    
total read_source_models 0.31496   0.0       2     
saving ruptures          0.02323   0.0       10    
total get_eid_rlz        0.00835   0.0       11    
store source model       0.00822   0.0       2     
store source_info        0.00192   0.0       1     
reading exposure         6.838E-04 0.0       1     
======================== ========= ========= ======