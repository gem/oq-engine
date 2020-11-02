classical damage hazard
=======================

============== ====================
checksum32     4_073_658_548       
date           2020-11-02T08:41:10 
engine_version 3.11.0-gitd13380ddb1
============== ====================

num_sites = 7, num_levels = 90, num_rlzs = 8

Parameters
----------
=============================== ==========================================
calculation_mode                'preclassical'                            
number_of_logic_tree_samples    0                                         
maximum_distance                {'default': [(1.0, 200.0), (10.0, 200.0)]}
investigation_time              1.0                                       
ses_per_logic_tree_path         1                                         
truncation_level                3.0                                       
rupture_mesh_spacing            2.0                                       
complex_fault_mesh_spacing      2.0                                       
width_of_mfd_bin                0.1                                       
area_source_discretization      10.0                                      
pointsource_distance            None                                      
ground_motion_correlation_model None                                      
minimum_intensity               {}                                        
random_seed                     24                                        
master_seed                     0                                         
ses_seed                        42                                        
=============================== ==========================================

Input files
-----------
======================= ========================================================================
Name                    File                                                                    
======================= ========================================================================
exposure                `exposure_model.xml <exposure_model.xml>`_                              
gsim_logic_tree         `gsim_logic_tree.xml <gsim_logic_tree.xml>`_                            
job_ini                 `job_haz.ini <job_haz.ini>`_                                            
nonstructural_fragility `nonstructural_fragility_model.xml <nonstructural_fragility_model.xml>`_
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_            
structural_fragility    `structural_fragility_model.xml <structural_fragility_model.xml>`_      
======================= ========================================================================

Composite source model
----------------------
====== =================== ============
grp_id gsim                rlzs        
====== =================== ============
0      [BooreAtkinson2008] [0, 1, 4, 5]
0      [ChiouYoungs2008]   [2, 3, 6, 7]
1      [AkkarBommer2010]   [0, 2]      
1      [ChiouYoungs2008]   [1, 3]      
2      [AkkarBommer2010]   [4, 6]      
2      [ChiouYoungs2008]   [5, 7]      
====== =================== ============

Required parameters per tectonic region type
--------------------------------------------
===== ========================================= =========== ======================= =================
et_id gsims                                     distances   siteparams              ruptparams       
===== ========================================= =========== ======================= =================
0     '[BooreAtkinson2008]' '[ChiouYoungs2008]' rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
1     '[BooreAtkinson2008]' '[ChiouYoungs2008]' rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
2     '[AkkarBommer2010]' '[ChiouYoungs2008]'   rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
3     '[AkkarBommer2010]' '[ChiouYoungs2008]'   rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
===== ========================================= =========== ======================= =================

Exposure model
--------------
=========== =
#assets     7
#taxonomies 3
=========== =

======== ========== ======= ====== === === =========
taxonomy num_assets mean    stddev min max num_sites
tax1     4          1.00000 0%     1   1   4        
tax2     2          1.00000 0%     1   1   2        
tax3     1          1.00000 nan    1   1   1        
*ALL*    7          1.00000 0%     1   1   7        
======== ========== ======= ====== === === =========

Slowest sources
---------------
========= ==== ========= ========= ============
source_id code calc_time num_sites eff_ruptures
========= ==== ========= ========= ============
1         S    0.00281   7         482         
2;0       S    0.00251   7         4           
2;1       X    1.743E-04 7         1           
========= ==== ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
S    0.00532  
X    1.743E-04
==== =========

Information about the tasks
---------------------------
================== ====== ======= ====== ========= =======
operation-duration counts mean    stddev min       max    
preclassical       3      0.00234 50%    6.757E-04 0.00332
read_source_model  2      0.00609 70%    0.00180   0.01037
================== ====== ======= ====== ========= =======

Data transfer
-------------
================= =============================== ========
task              sent                            received
read_source_model converter=664 B fname=220 B     13.69 KB
preclassical      srcs=14.45 KB srcfilter=4.82 KB 721 B   
================= =============================== ========

Slowest operations
------------------
========================= ========= ========= ======
calc_46551, maxmem=1.1 GB time_sec  memory_mb counts
========================= ========= ========= ======
importing inputs          1.09569   0.0       1     
composite source model    1.06089   0.0       1     
total read_source_model   0.01218   0.64062   2     
total preclassical        0.00702   0.46094   3     
reading exposure          6.764E-04 0.0       1     
========================= ========= ========= ======