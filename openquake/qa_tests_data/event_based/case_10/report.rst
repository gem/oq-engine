Event Based Bogota
==================

============== ===================
checksum32     2,254,739,311      
date           2019-05-10T05:07:26
engine_version 3.5.0-gitbaeb4c1e35
============== ===================

num_sites = 5, num_levels = 104, num_rlzs = ?

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
====== ========= ==== ===== ===== ============ ========= ========= ======
grp_id source_id code gidx1 gidx2 num_ruptures calc_time num_sites weight
====== ========= ==== ===== ===== ============ ========= ========= ======
1      CC_67_175 P    241   242   63           0.0       0.0       0.0   
1      CC_67_174 P    240   241   63           0.0       0.0       0.0   
1      CC_67_173 P    239   240   63           0.0       0.0       0.0   
1      CC_67_172 P    238   239   63           0.0       0.0       0.0   
1      CC_67_171 P    237   238   63           0.0       0.0       0.0   
1      CC_67_170 P    236   237   63           0.0       0.0       0.0   
1      CC_67_168 P    235   236   63           0.0       0.0       0.0   
1      CC_67_167 P    234   235   63           0.0       0.0       0.0   
1      CC_66_83  P    233   234   30           0.0       0.0       0.0   
1      CC_66_82  P    232   233   30           0.0       0.0       0.0   
1      CC_64_412 P    231   232   84           0.0       0.0       0.0   
1      CC_64_411 P    230   231   84           0.0       0.0       0.0   
1      CC_64_410 P    229   230   84           0.0       0.0       0.0   
1      CC_64_41  P    228   229   84           0.0       0.0       0.0   
1      CC_64_409 P    227   228   84           0.0       0.0       0.0   
1      CC_64_408 P    226   227   84           0.0       0.0       0.0   
1      CC_64_407 P    225   226   84           0.0       0.0       0.0   
1      CC_64_406 P    224   225   84           0.0       0.0       0.0   
1      CC_64_405 P    223   224   84           0.0       0.0       0.0   
1      CC_64_404 P    222   223   84           0.0       0.0       0.0   
====== ========= ==== ===== ===== ============ ========= ========= ======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
C    0.0       1     
P    0.0       122   
==== ========= ======

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
read_source_models 0.23045 0.25477 0.05030 0.41060 2      
================== ======= ======= ======= ======= =======

Data transfer
-------------
================== ============================ ========
task               sent                         received
read_source_models converter=626 B fnames=241 B 70.47 KB
================== ============================ ========

Slowest operations
------------------
======================== ========= ========= ======
operation                time_sec  memory_mb counts
======================== ========= ========= ======
total read_source_models 0.46090   0.99609   2     
reading exposure         5.875E-04 0.0       1     
======================== ========= ========= ======