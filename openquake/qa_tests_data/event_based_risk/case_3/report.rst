Event Based Risk Lisbon
=======================

============== ====================
checksum32     2_099_960_623       
date           2020-11-02T09:14:18 
engine_version 3.11.0-git24d6ba92cd
============== ====================

num_sites = 1, num_levels = 1, num_rlzs = 8

Parameters
----------
=============================== ==========================================
calculation_mode                'preclassical'                            
number_of_logic_tree_samples    0                                         
maximum_distance                {'default': [(1.0, 400.0), (10.0, 400.0)]}
investigation_time              5.0                                       
ses_per_logic_tree_path         1                                         
truncation_level                5.0                                       
rupture_mesh_spacing            4.0                                       
complex_fault_mesh_spacing      4.0                                       
width_of_mfd_bin                0.1                                       
area_source_discretization      20.0                                      
pointsource_distance            None                                      
ground_motion_correlation_model None                                      
minimum_intensity               {}                                        
random_seed                     23                                        
master_seed                     42                                        
ses_seed                        42                                        
=============================== ==========================================

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
====== ===================== ======
grp_id gsim                  rlzs  
====== ===================== ======
0      '[AkkarBommer2010]'   [2, 3]
0      '[AtkinsonBoore2006]' [0, 1]
1      '[AkkarBommer2010]'   [6, 7]
1      '[AtkinsonBoore2006]' [4, 5]
2      '[AkkarBommer2010]'   [1, 3]
2      '[AtkinsonBoore2006]' [0, 2]
3      '[AkkarBommer2010]'   [5, 7]
3      '[AtkinsonBoore2006]' [4, 6]
====== ===================== ======

Required parameters per tectonic region type
--------------------------------------------
===== ========================================= ========= ========== ==========
et_id gsims                                     distances siteparams ruptparams
===== ========================================= ========= ========== ==========
0     '[AkkarBommer2010]' '[AtkinsonBoore2006]' rjb rrup  vs30       mag rake  
1     '[AkkarBommer2010]' '[AtkinsonBoore2006]' rjb rrup  vs30       mag rake  
2     '[AkkarBommer2010]' '[AtkinsonBoore2006]' rjb rrup  vs30       mag rake  
3     '[AkkarBommer2010]' '[AtkinsonBoore2006]' rjb rrup  vs30       mag rake  
===== ========================================= ========= ========== ==========

Exposure model
--------------
=========== =
#assets     1
#taxonomies 1
=========== =

======== ========== ======= ====== === === =========
taxonomy num_assets mean    stddev min max num_sites
M1_2_PC  1          1.00000 nan    1   1   1        
======== ========== ======= ====== === === =========

Slowest sources
---------------
========= ==== ========= ========= ============
source_id code calc_time num_sites eff_ruptures
========= ==== ========= ========= ============
0;0       A    1.423E-04 1         6_075       
10;1      A    1.302E-04 1         1_116       
4;0       A    1.299E-04 1         310         
10;0      A    1.276E-04 1         1_116       
2;0       A    1.273E-04 1         4_901       
1;1       A    1.268E-04 1         989         
6;1       A    1.256E-04 1         1_054       
4;1       A    1.254E-04 1         310         
6;0       A    1.252E-04 1         1_054       
8;0       A    1.245E-04 1         342         
8;1       A    1.099E-04 1         342         
3;1       A    7.439E-05 1         812         
5;1       A    7.391E-05 1         551         
1;0       A    7.391E-05 1         989         
9;1       A    7.367E-05 1         612         
7;1       A    7.367E-05 1         429         
0;1       A    7.367E-05 1         6_075       
5;0       A    7.343E-05 1         551         
2;1       A    7.176E-05 1         4_901       
7;0       A    7.153E-05 1         429         
========= ==== ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
A    0.00220  
==== =========

Information about the tasks
---------------------------
================== ====== ========= ====== ========= =========
operation-duration counts mean      stddev min       max      
preclassical       11     6.923E-04 4%     6.306E-04 7.370E-04
read_source_model  2      0.01162   0%     0.01157   0.01166  
================== ====== ========= ====== ========= =========

Data transfer
-------------
================= =============================== ========
task              sent                            received
read_source_model converter=664 B fname=212 B     12.46 KB
preclassical      srcs=32.54 KB srcfilter=30.6 KB 3.06 KB 
================= =============================== ========

Slowest operations
------------------
========================= ========= ========= ======
calc_46974, maxmem=1.5 GB time_sec  memory_mb counts
========================= ========= ========= ======
importing inputs          1.56336   0.0       1     
composite source model    1.54480   0.0       1     
total read_source_model   0.02324   0.51172   2     
total preclassical        0.00761   0.37109   11    
reading exposure          6.163E-04 0.0       1     
========================= ========= ========= ======