Classical PSHA with source specific logic tree (3**2 realizations)
==================================================================

============== ===================
checksum32     3_958_530_442      
date           2020-01-16T05:31:48
engine_version 3.8.0-git83c45f7244
============== ===================

num_sites = 1, num_levels = 14, num_rlzs = 9

Parameters
----------
=============================== ==================
calculation_mode                'preclassical'    
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              50.0              
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            5.0               
complex_fault_mesh_spacing      5.0               
width_of_mfd_bin                0.1               
area_source_discretization      10.0              
pointsource_distance            None              
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
=========== ======= =============== ================
smlt_path   weight  gsim_logic_tree num_realizations
=========== ======= =============== ================
b11_b21_b31 0.11089 trivial(1,1)    1               
b11_b21_b32 0.11089 trivial(1,1)    1               
b11_b21_b33 0.11122 trivial(1,1)    1               
b11_b22_b31 0.11089 trivial(1,1)    1               
b11_b22_b32 0.11089 trivial(1,1)    1               
b11_b22_b33 0.11122 trivial(1,1)    1               
b11_b23_b31 0.11122 trivial(1,1)    1               
b11_b23_b32 0.11122 trivial(1,1)    1               
b11_b23_b33 0.11156 trivial(1,1)    1               
=========== ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ===================== ========= ========== ==========
grp_id gsims                 distances siteparams ruptparams
====== ===================== ========= ========== ==========
0      '[BooreAtkinson2008]' rjb       vs30       mag rake  
1      '[ToroEtAl2002]'      rjb                  mag       
2      '[BooreAtkinson2008]' rjb       vs30       mag rake  
3      '[ToroEtAl2002]'      rjb                  mag       
4      '[BooreAtkinson2008]' rjb       vs30       mag rake  
5      '[ToroEtAl2002]'      rjb                  mag       
6      '[BooreAtkinson2008]' rjb       vs30       mag rake  
7      '[ToroEtAl2002]'      rjb                  mag       
8      '[BooreAtkinson2008]' rjb       vs30       mag rake  
9      '[ToroEtAl2002]'      rjb                  mag       
10     '[BooreAtkinson2008]' rjb       vs30       mag rake  
11     '[ToroEtAl2002]'      rjb                  mag       
12     '[BooreAtkinson2008]' rjb       vs30       mag rake  
13     '[ToroEtAl2002]'      rjb                  mag       
14     '[BooreAtkinson2008]' rjb       vs30       mag rake  
15     '[ToroEtAl2002]'      rjb                  mag       
16     '[BooreAtkinson2008]' rjb       vs30       mag rake  
17     '[ToroEtAl2002]'      rjb                  mag       
====== ===================== ========= ========== ==========

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=18, rlzs=9)>

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      0.03226   310          310         
1      0.05000   1_040        1_040       
2      0.03226   310          310         
3      NaN       1_040        0.0         
4      0.03226   310          310         
5      NaN       1_040        0.0         
6      NaN       310          0.0         
7      0.05000   1_040        1_040       
8      NaN       310          0.0         
9      NaN       1_040        0.0         
10     NaN       310          0.0         
11     NaN       1_040        0.0         
12     NaN       310          0.0         
13     0.05000   1_040        1_040       
14     NaN       310          0.0         
15     NaN       1_040        0.0         
16     NaN       310          0.0         
17     NaN       1_040        0.0         
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
2         4      S    310          0.02231   0.03226   310         
2         2      S    310          0.02196   0.03226   310         
2         0      S    310          0.02112   0.03226   310         
1         13     A    1_040        0.00729   0.05000   1_040       
1         7      A    1_040        0.00710   0.05000   1_040       
1         1      A    1_040        0.00643   0.05000   1_040       
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
A    0.02082  
S    0.06538  
==== =========

Duplicated sources
------------------
Found 0 unique sources and 6 duplicate sources with multiplicity 3.0: ['1' '1' '1' '2' '2' '2']

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
SourceReader       0.04456 0.00368 0.04041 0.04983 9      
preclassical       0.02546 0.00274 0.02223 0.02839 6      
================== ======= ======= ======= ======= =======

Data transfer
-------------
============ ============================================== ========
task         sent                                           received
SourceReader apply_unc=14.38 KB ltmodel=1.76 KB fname=936 B 38.91 KB
preclassical srcs=9.33 KB params=4.41 KB srcfilter=1.31 KB  2.2 KB  
============ ============================================== ========

Slowest operations
------------------
=========================== ======== ========= ======
calc_43326                  time_sec memory_mb counts
=========================== ======== ========= ======
total SourceReader          0.40101  0.0       9     
total preclassical          0.15279  0.0       6     
composite source model      0.10777  0.0       1     
splitting/filtering sources 0.06135  0.0       6     
store source_info           0.00256  0.0       1     
aggregate curves            0.00142  0.0       6     
=========================== ======== ========= ======