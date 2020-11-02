Classical Hazard-Risk QA test 4
===============================

============== ====================
checksum32     204_296_531         
date           2020-11-02T09:12:50 
engine_version 3.11.0-git24d6ba92cd
============== ====================

num_sites = 6, num_levels = 19, num_rlzs = 2

Parameters
----------
=============================== ==========================================
calculation_mode                'preclassical'                            
number_of_logic_tree_samples    0                                         
maximum_distance                {'default': [(1.0, 200.0), (10.0, 200.0)]}
investigation_time              50.0                                      
ses_per_logic_tree_path         1                                         
truncation_level                3.0                                       
rupture_mesh_spacing            5.0                                       
complex_fault_mesh_spacing      5.0                                       
width_of_mfd_bin                0.2                                       
area_source_discretization      10.0                                      
pointsource_distance            None                                      
ground_motion_correlation_model None                                      
minimum_intensity               {}                                        
random_seed                     23                                        
master_seed                     0                                         
ses_seed                        42                                        
=============================== ==========================================

Input files
-----------
======================== ============================================================
Name                     File                                                        
======================== ============================================================
exposure                 `exposure_model.xml <exposure_model.xml>`_                  
gsim_logic_tree          `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                  `job_haz.ini <job_haz.ini>`_                                
source_model_logic_tree  `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
structural_vulnerability `vulnerability_model.xml <vulnerability_model.xml>`_        
======================== ============================================================

Composite source model
----------------------
====== =================== ====
grp_id gsim                rlzs
====== =================== ====
0      '[AkkarBommer2010]' [0] 
0      '[ChiouYoungs2008]' [1] 
====== =================== ====

Required parameters per tectonic region type
--------------------------------------------
===== ======================================= =========== ======================= =================
et_id gsims                                   distances   siteparams              ruptparams       
===== ======================================= =========== ======================= =================
0     '[AkkarBommer2010]' '[ChiouYoungs2008]' rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
===== ======================================= =========== ======================= =================

Exposure model
--------------
=========== =
#assets     6
#taxonomies 2
=========== =

======== ========== ======= ====== === === =========
taxonomy num_assets mean    stddev min max num_sites
W        5          1.00000 0%     1   1   5        
A        1          1.00000 nan    1   1   1        
*ALL*    6          1.00000 0%     1   1   6        
======== ========== ======= ====== === === =========

Slowest sources
---------------
========= ==== ========= ========= ============
source_id code calc_time num_sites eff_ruptures
========= ==== ========= ========= ============
376       A    1.364E-04 1         2_220       
231       A    6.747E-05 6         4_185       
========= ==== ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
A    2.038E-04
==== =========

Information about the tasks
---------------------------
================== ====== ========= ====== ========= =========
operation-duration counts mean      stddev min       max      
preclassical       13     6.810E-04 4%     6.208E-04 7.398E-04
read_source_model  1      0.12356   nan    0.12356   0.12356  
================== ====== ========= ====== ========= =========

Data transfer
-------------
================= ================================ ========
task              sent                             received
read_source_model                                  19.31 KB
preclassical      srcs=51.03 KB srcfilter=19.83 KB 2.59 KB 
================= ================================ ========

Slowest operations
------------------
========================= ========= ========= ======
calc_46858, maxmem=1.5 GB time_sec  memory_mb counts
========================= ========= ========= ======
importing inputs          4.87288   0.44531   1     
composite source model    4.84618   0.42578   1     
total read_source_model   0.12356   0.34766   1     
total preclassical        0.00885   0.41016   13    
reading exposure          5.276E-04 0.0       1     
========================= ========= ========= ======