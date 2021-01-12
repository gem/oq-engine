applyToSources with multiple sources
====================================

============== ====================
checksum32     3_933_251_036       
date           2020-11-02T09:37:16 
engine_version 3.11.0-git82b78631ac
============== ====================

num_sites = 1, num_levels = 1, num_rlzs = 9

Parameters
----------
=============================== ==================================================================================================================================================================================================================
calculation_mode                'preclassical'                                                                                                                                                                                                    
number_of_logic_tree_samples    9                                                                                                                                                                                                                 
maximum_distance                {'Active Shallow Crust': [(1.0, 30.0), (10.0, 30.0)], 'Stable Continental Interior': [(1.0, 30.0), (10.0, 30.0)], 'Subduction Interface': [(1.0, 100.0), (10.0, 100.0)], 'default': [(1.0, 100.0), (10.0, 100.0)]}
investigation_time              1.0                                                                                                                                                                                                               
ses_per_logic_tree_path         1                                                                                                                                                                                                                 
truncation_level                None                                                                                                                                                                                                              
rupture_mesh_spacing            5.0                                                                                                                                                                                                               
complex_fault_mesh_spacing      50.0                                                                                                                                                                                                              
width_of_mfd_bin                0.5                                                                                                                                                                                                               
area_source_discretization      50.0                                                                                                                                                                                                              
pointsource_distance            {'default': [(1.0, 0), (10.0, 0)]}                                                                                                                                                                                
ground_motion_correlation_model None                                                                                                                                                                                                              
minimum_intensity               {}                                                                                                                                                                                                                
random_seed                     42                                                                                                                                                                                                                
master_seed                     0                                                                                                                                                                                                                 
ses_seed                        42                                                                                                                                                                                                                
=============================== ==================================================================================================================================================================================================================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gsim_logic_tree.xml <gsim_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
====== ====================== =========
grp_id gsim                   rlzs     
====== ====================== =========
0      '[SadighEtAl1997]'     [0, 4, 5]
1      '[SadighEtAl1997]'     [1, 2]   
2      '[SadighEtAl1997]'     [3, 7]   
3      '[SadighEtAl1997]'     [6]      
4      '[SadighEtAl1997]'     [8]      
5      '[SadighEtAl1997]'     [0, 1]   
6      '[SadighEtAl1997]'     [2]      
7      '[SadighEtAl1997]'     [3]      
8      '[SadighEtAl1997]'     [4, 5]   
9      '[SadighEtAl1997]'     [6, 7]   
10     '[SadighEtAl1997]'     [8]      
11     '[SadighEtAl1997]'     [0, 1]   
11     '[AkkarBommer2010]'    [2]      
12     '[SadighEtAl1997]'     [0, 1]   
12     '[AkkarBommer2010]'    [2, 3]   
13     '[SadighEtAl1997]'     [0]      
13     '[AkkarBommer2010]'    [2]      
14     '[SadighEtAl1997]'     [0]      
14     '[AkkarBommer2010]'    [2, 3]   
15     '[SadighEtAl1997]'     [0, 6]   
16     '[SadighEtAl1997]'     [1]      
17     '[SadighEtAl1997]'     [1, 5, 8]
17     '[AkkarBommer2010]'    [2]      
18     '[SadighEtAl1997]'     [1]      
18     '[AkkarBommer2010]'    [3]      
19     '[AkkarBommer2010]'    [3]      
20     '[SadighEtAl1997]'     [4]      
21     '[SadighEtAl1997]'     [4, 5]   
22     '[SadighEtAl1997]'     [5]      
23     '[SadighEtAl1997]'     [6]      
23     '[CauzziFaccioli2008]' [7]      
24     '[SadighEtAl1997]'     [6, 8]   
24     '[CauzziFaccioli2008]' [7]      
25     '[SadighEtAl1997]'     [6, 8]   
26     '[CauzziFaccioli2008]' [7]      
27     '[SadighEtAl1997]'     [8]      
====== ====================== =========

Required parameters per tectonic region type
--------------------------------------------
===== ============================================================= ============== ========== ==========
et_id gsims                                                         distances      siteparams ruptparams
===== ============================================================= ============== ========== ==========
0     '[AkkarBommer2010]' '[CauzziFaccioli2008]' '[SadighEtAl1997]' rhypo rjb rrup vs30       mag rake  
1     '[AkkarBommer2010]' '[CauzziFaccioli2008]' '[SadighEtAl1997]' rhypo rjb rrup vs30       mag rake  
2     '[AkkarBommer2010]' '[CauzziFaccioli2008]' '[SadighEtAl1997]' rhypo rjb rrup vs30       mag rake  
3     '[AkkarBommer2010]' '[CauzziFaccioli2008]' '[SadighEtAl1997]' rhypo rjb rrup vs30       mag rake  
4     '[AkkarBommer2010]' '[CauzziFaccioli2008]' '[SadighEtAl1997]' rhypo rjb rrup vs30       mag rake  
5     '[AkkarBommer2010]' '[CauzziFaccioli2008]' '[SadighEtAl1997]' rhypo rjb rrup vs30       mag rake  
6     '[AkkarBommer2010]' '[CauzziFaccioli2008]' '[SadighEtAl1997]' rhypo rjb rrup vs30       mag rake  
7     '[AkkarBommer2010]' '[CauzziFaccioli2008]' '[SadighEtAl1997]' rhypo rjb rrup vs30       mag rake  
8     '[AkkarBommer2010]' '[CauzziFaccioli2008]' '[SadighEtAl1997]' rhypo rjb rrup vs30       mag rake  
9     '[SadighEtAl1997]'                                            rrup           vs30       mag rake  
10    '[SadighEtAl1997]'                                            rrup           vs30       mag rake  
11    '[SadighEtAl1997]'                                            rrup           vs30       mag rake  
12    '[SadighEtAl1997]'                                            rrup           vs30       mag rake  
13    '[SadighEtAl1997]'                                            rrup           vs30       mag rake  
14    '[SadighEtAl1997]'                                            rrup           vs30       mag rake  
15    '[SadighEtAl1997]'                                            rrup           vs30       mag rake  
16    '[SadighEtAl1997]'                                            rrup           vs30       mag rake  
17    '[SadighEtAl1997]'                                            rrup           vs30       mag rake  
18    '[SadighEtAl1997]'                                            rrup           vs30       mag rake  
19    '[SadighEtAl1997]'                                            rrup           vs30       mag rake  
20    '[SadighEtAl1997]'                                            rrup           vs30       mag rake  
21    '[SadighEtAl1997]'                                            rrup           vs30       mag rake  
22    '[SadighEtAl1997]'                                            rrup           vs30       mag rake  
23    '[SadighEtAl1997]'                                            rrup           vs30       mag rake  
24    '[SadighEtAl1997]'                                            rrup           vs30       mag rake  
25    '[SadighEtAl1997]'                                            rrup           vs30       mag rake  
26    '[SadighEtAl1997]'                                            rrup           vs30       mag rake  
===== ============================================================= ============== ========== ==========

Slowest sources
---------------
========= ==== ========= ========= ============
source_id code calc_time num_sites eff_ruptures
========= ==== ========= ========= ============
1;1       C    0.00392   1         633         
1;4       C    0.00362   1         633         
1;0       C    0.00360   1         633         
1;2       C    0.00356   1         633         
1;3       C    0.00355   1         656         
1;5       C    0.00323   1         633         
========= ==== ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
A    0.0      
C    0.02148  
S    0.0      
==== =========

Information about the tasks
---------------------------
================== ====== ======= ====== ========= =======
operation-duration counts mean    stddev min       max    
preclassical       16     0.00513 73%    6.669E-04 0.01157
read_source_model  1      0.02007 nan    0.02007   0.02007
================== ====== ======= ====== ========= =======

Data transfer
-------------
================= ================================ ========
task              sent                             received
read_source_model                                  12.36 KB
preclassical      srcs=96.25 KB srcfilter=25.16 KB 3.33 KB 
================= ================================ ========

Slowest operations
------------------
========================= ======== ========= ======
calc_47354, maxmem=1.5 GB time_sec memory_mb counts
========================= ======== ========= ======
importing inputs          1.70292  0.0       1     
composite source model    1.69666  0.0       1     
total preclassical        0.08200  0.39844   16    
total read_source_model   0.02007  0.0       1     
========================= ======== ========= ======