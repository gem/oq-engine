Classical BCR test
==================

============== ====================
checksum32     4_073_231_028       
date           2020-11-02T09:35:26 
engine_version 3.11.0-git82b78631ac
============== ====================

num_sites = 11, num_levels = 30, num_rlzs = 3

Parameters
----------
=============================== ==========================================
calculation_mode                'preclassical'                            
number_of_logic_tree_samples    0                                         
maximum_distance                {'default': [(1.0, 200.0), (10.0, 200.0)]}
investigation_time              50.0                                      
ses_per_logic_tree_path         1                                         
truncation_level                3.0                                       
rupture_mesh_spacing            20.0                                      
complex_fault_mesh_spacing      20.0                                      
width_of_mfd_bin                0.5                                       
area_source_discretization      20.0                                      
pointsource_distance            None                                      
ground_motion_correlation_model None                                      
minimum_intensity               {}                                        
random_seed                     42                                        
master_seed                     0                                         
ses_seed                        42                                        
=============================== ==========================================

Input files
-----------
==================================== ============================================================================
Name                                 File                                                                        
==================================== ============================================================================
exposure                             `exposure_model.xml <exposure_model.xml>`_                                  
gsim_logic_tree                      `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                                
job_ini                              `job.ini <job.ini>`_                                                        
source_model_logic_tree              `source_model_logic_tree.xml <source_model_logic_tree.xml>`_                
structural_vulnerability             `structural_vulnerability_model.xml <structural_vulnerability_model.xml>`_  
structural_vulnerability_retrofitted `vulnerability_model_retrofitted.xml <vulnerability_model_retrofitted.xml>`_
==================================== ============================================================================

Composite source model
----------------------
====== ===================== ====
grp_id gsim                  rlzs
====== ===================== ====
0      '[AkkarBommer2010]'   [2] 
0      '[BooreAtkinson2008]' [1] 
0      '[ChiouYoungs2008]'   [0] 
====== ===================== ====

Required parameters per tectonic region type
--------------------------------------------
===== ============================================================= =========== ======================= =================
et_id gsims                                                         distances   siteparams              ruptparams       
===== ============================================================= =========== ======================= =================
0     '[AkkarBommer2010]' '[BooreAtkinson2008]' '[ChiouYoungs2008]' rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
===== ============================================================= =========== ======================= =================

Exposure model
--------------
=========== ==
#assets     11
#taxonomies 4 
=========== ==

========================== ========== ======= ====== === === =========
taxonomy                   num_assets mean    stddev min max num_sites
Adobe                      2          1.00000 0%     1   1   2        
Stone-Masonry              6          1.00000 0%     1   1   6        
Unreinforced-Brick-Masonry 1          1.00000 nan    1   1   1        
Wood                       2          1.00000 0%     1   1   2        
*ALL*                      11         1.00000 0%     1   1   11       
========================== ========== ======= ====== === === =========

Slowest sources
---------------
========= ==== ========= ========= ============
source_id code calc_time num_sites eff_ruptures
========= ==== ========= ========= ============
229       A    1.752E-04 7         264         
231       A    1.726E-04 11        414         
232       A    1.323E-04 11        150         
========= ==== ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
A    4.802E-04
==== =========

Information about the tasks
---------------------------
================== ====== ========= ====== ========= =========
operation-duration counts mean      stddev min       max      
preclassical       3      6.601E-04 1%     6.554E-04 6.695E-04
read_source_model  1      0.00462   nan    0.00462   0.00462  
================== ====== ========= ====== ========= =========

Data transfer
-------------
================= ============================== ========
task              sent                           received
read_source_model                                2.61 KB 
preclassical      srcs=6.11 KB srcfilter=4.54 KB 723 B   
================= ============================== ========

Slowest operations
------------------
========================= ========= ========= ======
calc_47206, maxmem=1.1 GB time_sec  memory_mb counts
========================= ========= ========= ======
importing inputs          0.28921   0.12109   1     
composite source model    0.23668   0.12109   1     
total read_source_model   0.00462   0.0       1     
total preclassical        0.00198   0.44922   3     
reading exposure          7.265E-04 0.0       1     
========================= ========= ========= ======