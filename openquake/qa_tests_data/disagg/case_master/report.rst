disaggregation with a complex logic tree
========================================

============== ====================
checksum32     1_264_132_805       
date           2020-11-02T09:13:11 
engine_version 3.11.0-git24d6ba92cd
============== ====================

num_sites = 2, num_levels = 100, num_rlzs = 8

Parameters
----------
=============================== ========================================
calculation_mode                'preclassical'                          
number_of_logic_tree_samples    0                                       
maximum_distance                {'default': [(1.0, 60.0), (10.0, 60.0)]}
investigation_time              50.0                                    
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
=============================== ========================================

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
====== ===================== ============
grp_id gsim                  rlzs        
====== ===================== ============
0      '[BooreAtkinson2008]' [0, 1, 4, 5]
0      '[ChiouYoungs2008]'   [2, 3, 6, 7]
1      '[AkkarBommer2010]'   [0, 2]      
1      '[ChiouYoungs2008]'   [1, 3]      
2      '[AkkarBommer2010]'   [4, 6]      
2      '[ChiouYoungs2008]'   [5, 7]      
====== ===================== ============

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

Slowest sources
---------------
========= ==== ========= ========= ============
source_id code calc_time num_sites eff_ruptures
========= ==== ========= ========= ============
1         S    0.00268   2         543         
2;0       S    0.00259   2         4           
2;1       X    1.974E-04 2         1           
========= ==== ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
S    0.00527  
X    1.974E-04
==== =========

Information about the tasks
---------------------------
================== ====== ======= ====== ========= =======
operation-duration counts mean    stddev min       max    
preclassical       3      0.00232 49%    6.804E-04 0.00317
read_source_model  2      0.00625 71%    0.00180   0.01070
================== ====== ======= ====== ========= =======

Data transfer
-------------
================= =============================== ========
task              sent                            received
read_source_model converter=664 B fname=200 B     13.67 KB
preclassical      srcs=14.45 KB srcfilter=4.01 KB 721 B   
================= =============================== ========

Slowest operations
------------------
========================= ======== ========= ======
calc_46898, maxmem=1.1 GB time_sec memory_mb counts
========================= ======== ========= ======
importing inputs          1.04757  0.01172   1     
composite source model    1.04266  0.01172   1     
total read_source_model   0.01250  0.47266   2     
total preclassical        0.00695  0.46875   3     
========================= ======== ========= ======