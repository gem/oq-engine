Event Based Bogota
==================

============== ===================
checksum32     2,709,362,541      
date           2018-10-05T03:04:47
engine_version 3.3.0-git48e9a474fd
============== ===================

num_sites = 5, num_levels = 104

Parameters
----------
=============================== ==================
calculation_mode                'event_based'     
number_of_logic_tree_samples    100               
maximum_distance                {'default': 100.0}
investigation_time              1.0               
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            5.0               
complex_fault_mesh_spacing      5.0               
width_of_mfd_bin                0.2               
area_source_discretization      10.0              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     113               
master_seed                     0                 
ses_seed                        42                
=============================== ==================

Input files
-----------
======================== ========================================================================
Name                     File                                                                    
======================== ========================================================================
exposure                 `exposure_model.xml <exposure_model.xml>`_                              
gsim_logic_tree          `logic_tree_gmpe_simplified.xml <logic_tree_gmpe_simplified.xml>`_      
job_ini                  `job.ini <job.ini>`_                                                    
site_model               `site_model_bog.xml <site_model_bog.xml>`_                              
source                   `source-gridded_seismicity_bog.xml <source-gridded_seismicity_bog.xml>`_
source                   `source-int_col_bog.xml <source-int_col_bog.xml>`_                      
source_model_logic_tree  `logic_tree_source_model.xml <logic_tree_source_model.xml>`_            
structural_vulnerability `vulnerability_model_bog.xml <vulnerability_model_bog.xml>`_            
======================== ========================================================================

Exposure model
--------------
=============== ========
#assets         5       
#taxonomies     4       
deductibile     absolute
insurance_limit absolute
=============== ========

===================== ======= ====== === === ========= ==========
taxonomy              mean    stddev min max num_sites num_assets
MCF/LWAL+DUC/HBET:3,6 1.00000 0.0    1   1   2         2         
MUR/HBET:4,5          1.00000 NaN    1   1   1         1         
CR/LDUAL+DUC          1.00000 NaN    1   1   1         1         
CR/LFINF+DUC          1.00000 NaN    1   1   1         1         
*ALL*                 1.00000 0.0    1   1   5         5         
===================== ======= ====== === === ========= ==========

Slowest sources
---------------
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======
grp_id source_id code gidx1 gidx2 num_ruptures calc_time split_time num_sites num_split weight
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======
0      0         C    0     120   5,370        0.0       0.0        0.0       0         0.0   
1      CC_02_147 P    0     1     108          0.0       8.345E-06  0.0       1         0.0   
1      CC_02_148 P    1     2     108          0.0       3.099E-06  0.0       1         0.0   
1      CC_02_149 P    2     3     108          0.0       1.907E-06  0.0       1         0.0   
1      CC_02_15  P    3     4     108          0.0       2.146E-06  0.0       1         0.0   
1      CC_02_150 P    4     5     108          0.0       1.669E-06  0.0       1         0.0   
1      CC_02_151 P    5     6     108          0.0       1.669E-06  0.0       1         0.0   
1      CC_02_152 P    6     7     108          0.0       1.907E-06  0.0       1         0.0   
1      CC_02_153 P    7     8     108          0.0       1.907E-06  0.0       1         0.0   
1      CC_02_37  P    8     9     108          0.0       1.669E-06  0.0       1         0.0   
1      CC_02_374 P    9     10    108          0.0       1.669E-06  0.0       1         0.0   
1      CC_02_375 P    10    11    108          0.0       1.669E-06  0.0       1         0.0   
1      CC_02_376 P    11    12    108          0.0       1.907E-06  0.0       1         0.0   
1      CC_02_377 P    12    13    108          0.0       1.907E-06  0.0       1         0.0   
1      CC_02_38  P    13    14    108          0.0       3.099E-06  0.0       1         0.0   
1      CC_02_39  P    14    15    108          0.0       1.431E-06  0.0       1         0.0   
1      CC_02_58  P    15    16    108          0.0       1.431E-06  0.0       1         0.0   
1      CC_02_59  P    16    17    108          0.0       1.907E-06  0.0       1         0.0   
1      CC_02_60  P    17    18    108          0.0       1.907E-06  0.0       1         0.0   
1      CC_02_61  P    18    19    108          0.0       1.669E-06  0.0       1         0.0   
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
C    0.0       1     
P    0.0       122   
==== ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
read_source_models 0.25784 0.29811 0.04704 0.46863 2      
split_filter       0.05421 0.06350 0.00931 0.09911 2      
================== ======= ======= ======= ======= =======

Data transfer
-------------
================== ========================================================================= =========
task               sent                                                                      received 
read_source_models monitor=662 B converter=638 B fnames=391 B                                67.36 KB 
split_filter       srcs=127.16 KB monitor=686 B srcfilter=440 B sample_factor=42 B seed=28 B 107.07 KB
================== ========================================================================= =========

Slowest operations
------------------
======================== ========= ========= ======
operation                time_sec  memory_mb counts
======================== ========= ========= ======
total read_source_models 0.51567   1.59375   2     
updating source_info     0.11286   0.0       1     
total split_filter       0.10842   0.0       2     
reading exposure         5.357E-04 0.0       1     
======================== ========= ========= ======