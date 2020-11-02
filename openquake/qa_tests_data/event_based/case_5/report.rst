Germany_SHARE Combined Model event_based
========================================

============== ====================
checksum32     4_289_007_873       
date           2020-11-02T09:13:35 
engine_version 3.11.0-git24d6ba92cd
============== ====================

num_sites = 100, num_levels = 1, num_rlzs = 15

Parameters
----------
=============================== ========================================
calculation_mode                'preclassical'                          
number_of_logic_tree_samples    0                                       
maximum_distance                {'default': [(1.0, 80.0), (10.0, 80.0)]}
investigation_time              30.0                                    
ses_per_logic_tree_path         1                                       
truncation_level                3.0                                     
rupture_mesh_spacing            5.0                                     
complex_fault_mesh_spacing      5.0                                     
width_of_mfd_bin                0.1                                     
area_source_discretization      18.0                                    
pointsource_distance            None                                    
ground_motion_correlation_model None                                    
minimum_intensity               {}                                      
random_seed                     42                                      
master_seed                     0                                       
ses_seed                        23                                      
=============================== ========================================

Input files
-----------
======================= ==============================================================================
Name                    File                                                                          
======================= ==============================================================================
gsim_logic_tree         `complete_gmpe_logic_tree.xml <complete_gmpe_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                                          
sites                   `sites.csv <sites.csv>`_                                                      
source_model_logic_tree `combined_logic-tree-source-model.xml <combined_logic-tree-source-model.xml>`_
======================= ==============================================================================

Composite source model
----------------------
====== ====================== ====================
grp_id gsim                   rlzs                
====== ====================== ====================
0      '[FaccioliEtAl2010]'   [0, 1, 2, 3, 4]     
1      '[FaccioliEtAl2010]'   [10, 11, 12, 13, 14]
2      '[AkkarBommer2010]'    [5]                 
2      '[Campbell2003SHARE]'  [9]                 
2      '[CauzziFaccioli2008]' [6]                 
2      '[ChiouYoungs2008]'    [7]                 
2      '[ToroEtAl2002SHARE]'  [8]                 
====== ====================== ====================

Required parameters per tectonic region type
--------------------------------------------
===== ========================================================================================================== ================= ======================= =================
et_id gsims                                                                                                      distances         siteparams              ruptparams       
===== ========================================================================================================== ================= ======================= =================
0     '[AkkarBommer2010]' '[Campbell2003SHARE]' '[CauzziFaccioli2008]' '[ChiouYoungs2008]' '[ToroEtAl2002SHARE]' rhypo rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
1     '[AkkarBommer2010]' '[Campbell2003SHARE]' '[CauzziFaccioli2008]' '[ChiouYoungs2008]' '[ToroEtAl2002SHARE]' rhypo rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
2     '[AkkarBommer2010]' '[Campbell2003SHARE]' '[CauzziFaccioli2008]' '[ChiouYoungs2008]' '[ToroEtAl2002SHARE]' rhypo rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
3     '[FaccioliEtAl2010]'                                                                                       rrup              vs30                    mag rake         
4     '[FaccioliEtAl2010]'                                                                                       rrup              vs30                    mag rake         
5     '[FaccioliEtAl2010]'                                                                                       rrup              vs30                    mag rake         
===== ========================================================================================================== ================= ======================= =================

Slowest sources
---------------
========= ==== ========= ========= ============
source_id code calc_time num_sites eff_ruptures
========= ==== ========= ========= ============
19        S    0.01095   9         349         
20        S    0.00446   9         31          
22        S    0.00338   1         34          
21        S    0.00266   9         7           
330079    P    2.298E-04 11        12          
330067    P    2.196E-04 5         16          
330071    P    2.186E-04 9         12          
330063    P    2.153E-04 9         12          
330047    P    2.089E-04 8         26          
330051    P    2.086E-04 16        34          
330059    P    2.015E-04 6         14          
330075    P    2.003E-04 5         16          
330055    P    1.996E-04 6         24          
1         A    1.757E-04 8         7           
330045    P    1.459E-04 7         22          
257       A    1.416E-04 9         96          
330068    P    1.411E-04 5         18          
330072    P    1.392E-04 9         14          
330048    P    1.388E-04 8         28          
247       A    1.388E-04 10        156         
========= ==== ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
A    0.00142  
P    0.00524  
S    0.02144  
==== =========

Information about the tasks
---------------------------
================== ====== ======= ====== ========= =======
operation-duration counts mean    stddev min       max    
preclassical       14     0.00255 144%   5.615E-04 0.01198
read_source_model  3      0.01352 54%    0.00337   0.02039
================== ====== ======= ====== ========= =======

Data transfer
-------------
================= ================================= ========
task              sent                              received
read_source_model converter=1.05 KB fname=353 B     32.98 KB
preclassical      srcfilter=103.99 KB srcs=53.64 KB 5.04 KB 
================= ================================= ========

Slowest operations
------------------
========================= ======== ========= ======
calc_46936, maxmem=1.5 GB time_sec memory_mb counts
========================= ======== ========= ======
importing inputs          1.29566  0.05078   1     
composite source model    1.28995  0.05078   1     
total read_source_model   0.04057  0.60938   3     
total preclassical        0.03564  0.47656   14    
========================= ======== ========= ======