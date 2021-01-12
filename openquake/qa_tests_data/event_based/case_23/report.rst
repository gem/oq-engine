Example EB Hazard. Infer region from exposure model
===================================================

============== ====================
checksum32     2_604_032_785       
date           2020-11-02T09:36:25 
engine_version 3.11.0-git82b78631ac
============== ====================

num_sites = 93, num_levels = 0, num_rlzs = 2

Parameters
----------
=============================== ======================================
calculation_mode                'preclassical'                        
number_of_logic_tree_samples    0                                     
maximum_distance                {'default': [(1.0, 200), (10.0, 200)]}
investigation_time              1.0                                   
ses_per_logic_tree_path         5                                     
truncation_level                3.0                                   
rupture_mesh_spacing            5.0                                   
complex_fault_mesh_spacing      5.0                                   
width_of_mfd_bin                0.5                                   
area_source_discretization      10.0                                  
pointsource_distance            None                                  
ground_motion_correlation_model None                                  
minimum_intensity               {}                                    
random_seed                     42                                    
master_seed                     0                                     
ses_seed                        42                                    
=============================== ======================================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
exposure                `exposure_model.xml <exposure_model.xml>`_                  
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
site_model              `site_model.csv <site_model.csv>`_                          
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
====== =================== ====
grp_id gsim                rlzs
====== =================== ====
0      '[AkkarBommer2010]' [1] 
0      '[ChiouYoungs2008]' [0] 
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
=========== ==
#assets     96
#taxonomies 5 
=========== ==

========================== ========== ======= ====== === === =========
taxonomy                   num_assets mean    stddev min max num_sites
Wood                       23         1.00000 0%     1   1   23       
Adobe                      29         1.00000 0%     1   1   29       
Stone-Masonry              16         1.00000 0%     1   1   16       
Unreinforced-Brick-Masonry 27         1.00000 0%     1   1   27       
Concrete                   1          1.00000 nan    1   1   1        
*ALL*                      2_666      0.03601 533%   0   2   96       
========================== ========== ======= ====== === === =========

Slowest sources
---------------
========= ==== ========= ========= ============
source_id code calc_time num_sites eff_ruptures
========= ==== ========= ========= ============
236       A    1.979E-04 24        3_240       
232       A    1.740E-04 81        620         
279       A    1.738E-04 18        70          
224       A    1.729E-04 1         960         
228       A    1.724E-04 32        519         
230       A    1.712E-04 57        2_436       
239       A    1.681E-04 33        480         
234       A    1.667E-04 70        790         
226       A    1.602E-04 18        1_088       
243       A    1.476E-04 5         1_130       
238       A    1.378E-04 44        748         
374       A    1.323E-04 20        1_060       
386       A    1.194E-04 21        273         
231       A    1.168E-04 79        1_674       
235       A    1.161E-04 67        3_084       
233       A    1.156E-04 69        294         
240       A    1.132E-04 40        480         
229       A    1.097E-04 53        1_050       
376       A    1.059E-04 27        888         
227       A    1.020E-04 23        820         
========= ==== ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
A    0.00317  
==== =========

Information about the tasks
---------------------------
================== ====== ========= ====== ========= =========
operation-duration counts mean      stddev min       max      
preclassical       12     7.694E-04 11%    5.155E-04 8.929E-04
read_source_model  1      0.04168   nan    0.04168   0.04168  
================== ====== ========= ====== ========= =========

Data transfer
-------------
================= ================================ ========
task              sent                             received
read_source_model                                  11.44 KB
preclassical      srcfilter=71.17 KB srcs=34.39 KB 3.3 KB  
================= ================================ ========

Slowest operations
------------------
========================= ======== ========= ======
calc_47303, maxmem=1.5 GB time_sec memory_mb counts
========================= ======== ========= ======
importing inputs          3.60182  0.0       1     
composite source model    2.34377  0.0       1     
total read_source_model   0.04168  0.0       1     
reading exposure          0.01484  0.0       1     
total preclassical        0.00923  0.45312   12    
========================= ======== ========= ======