Event Based Bogota
==================

============== ===================
checksum32     2,254,739,311      
date           2019-01-20T07:38:05
engine_version 3.4.0-git452d0c6835
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
======================== ==================================================================
Name                     File                                                              
======================== ==================================================================
exposure                 `exposure_model.xml <exposure_model.xml>`_                        
gsim_logic_tree          `logic_tree_gmpe_simplified.xml <logic_tree_gmpe_simplified.xml>`_
job_ini                  `job.ini <job.ini>`_                                              
site_model               `site_model_bog.xml <site_model_bog.xml>`_                        
source_model_logic_tree  `logic_tree_source_model.xml <logic_tree_source_model.xml>`_      
structural_vulnerability `vulnerability_model_bog.xml <vulnerability_model_bog.xml>`_      
======================== ==================================================================

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
1      CC_02_147 P    120   121   108          0.0       0.0        0.0       1         0.0   
1      CC_02_148 P    121   122   108          0.0       0.0        0.0       1         0.0   
1      CC_02_149 P    122   123   108          0.0       0.0        0.0       1         0.0   
1      CC_02_15  P    123   124   108          0.0       0.0        0.0       1         0.0   
1      CC_02_150 P    124   125   108          0.0       0.0        0.0       1         0.0   
1      CC_02_151 P    125   126   108          0.0       0.0        0.0       1         0.0   
1      CC_02_152 P    126   127   108          0.0       0.0        0.0       1         0.0   
1      CC_02_153 P    127   128   108          0.0       0.0        0.0       1         0.0   
1      CC_02_37  P    128   129   108          0.0       0.0        0.0       1         0.0   
1      CC_02_374 P    129   130   108          0.0       0.0        0.0       1         0.0   
1      CC_02_375 P    130   131   108          0.0       0.0        0.0       1         0.0   
1      CC_02_376 P    131   132   108          0.0       0.0        0.0       1         0.0   
1      CC_02_377 P    132   133   108          0.0       0.0        0.0       1         0.0   
1      CC_02_38  P    133   134   108          0.0       0.0        0.0       1         0.0   
1      CC_02_39  P    134   135   108          0.0       0.0        0.0       1         0.0   
1      CC_02_58  P    135   136   108          0.0       0.0        0.0       1         0.0   
1      CC_02_59  P    136   137   108          0.0       0.0        0.0       1         0.0   
1      CC_02_60  P    137   138   108          0.0       0.0        0.0       1         0.0   
1      CC_02_61  P    138   139   108          0.0       0.0        0.0       1         0.0   
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
Found 0 source(s) with the same ID and 0 true duplicate(s)

Information about the tasks
---------------------------
================== ======= ========= ======= ======= =======
operation-duration mean    stddev    min     max     outputs
read_source_models 0.20295 0.23847   0.03433 0.37157 2      
split_filter       0.00976 1.094E-04 0.00968 0.00984 2      
================== ======= ========= ======= ======= =======

Data transfer
-------------
================== ======================================== ========
task               sent                                     received
read_source_models converter=776 B fnames=241 B             67.78 KB
split_filter       srcs=71.82 KB srcfilter=506 B dummy=28 B 70.25 KB
================== ======================================== ========

Slowest operations
------------------
======================== ========= ========= ======
operation                time_sec  memory_mb counts
======================== ========= ========= ======
total read_source_models 0.40590   1.78906   2     
total only_filter        0.01952   1.76953   2     
reading exposure         4.637E-04 0.0       1     
======================== ========= ========= ======