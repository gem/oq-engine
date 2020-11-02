Event Based Risk for Turkey reduced
===================================

============== ====================
checksum32     3_674_230_362       
date           2020-11-02T09:36:32 
engine_version 3.11.0-git82b78631ac
============== ====================

num_sites = 13, num_levels = 60, num_rlzs = 12

Parameters
----------
=============================== ==========================================
calculation_mode                'preclassical'                            
number_of_logic_tree_samples    0                                         
maximum_distance                {'default': [(1.0, 200.0), (10.0, 200.0)]}
investigation_time              10.0                                      
ses_per_logic_tree_path         1                                         
truncation_level                3.0                                       
rupture_mesh_spacing            4.0                                       
complex_fault_mesh_spacing      4.0                                       
width_of_mfd_bin                0.1                                       
area_source_discretization      20.0                                      
pointsource_distance            {'default': [(1.0, 0), (10.0, 0)]}        
ground_motion_correlation_model None                                      
minimum_intensity               {}                                        
random_seed                     323                                       
master_seed                     42                                        
ses_seed                        323                                       
=============================== ==========================================

Input files
-----------
======================== ==========================================================================
Name                     File                                                                      
======================== ==========================================================================
exposure                 `exposure.xml <exposure.xml>`_                                            
gsim_logic_tree          `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                              
job_ini                  `job.ini <job.ini>`_                                                      
site_model               `site_model.xml <site_model.xml>`_                                        
source_model_logic_tree  `source_model_logic_tree.xml <source_model_logic_tree.xml>`_              
structural_vulnerability `structural_vulnerability_model.xml <structural_vulnerability_model.xml>`_
======================== ==========================================================================

Composite source model
----------------------
====== ====================== ====
grp_id gsim                   rlzs
====== ====================== ====
0      '[AkkarBommer2010]'    [0] 
0      '[CauzziFaccioli2008]' [1] 
0      '[ChiouYoungs2008]'    [2] 
0      '[ZhaoEtAl2006Asc]'    [3] 
1      '[AkkarBommer2010]'    [4] 
1      '[CauzziFaccioli2008]' [5] 
1      '[ChiouYoungs2008]'    [6] 
1      '[ZhaoEtAl2006Asc]'    [7] 
2      '[AkkarBommer2010]'    [8] 
2      '[CauzziFaccioli2008]' [9] 
2      '[ChiouYoungs2008]'    [10]
2      '[ZhaoEtAl2006Asc]'    [11]
====== ====================== ====

Required parameters per tectonic region type
--------------------------------------------
===== ================================================================================== ================= ======================= ============================
et_id gsims                                                                              distances         siteparams              ruptparams                  
===== ================================================================================== ================= ======================= ============================
0     '[AkkarBommer2010]' '[CauzziFaccioli2008]' '[ChiouYoungs2008]' '[ZhaoEtAl2006Asc]' rhypo rjb rrup rx vs30 vs30measured z1pt0 dip hypo_depth mag rake ztor
1     '[AkkarBommer2010]' '[CauzziFaccioli2008]' '[ChiouYoungs2008]' '[ZhaoEtAl2006Asc]' rhypo rjb rrup rx vs30 vs30measured z1pt0 dip hypo_depth mag rake ztor
2     '[AkkarBommer2010]' '[CauzziFaccioli2008]' '[ChiouYoungs2008]' '[ZhaoEtAl2006Asc]' rhypo rjb rrup rx vs30 vs30measured z1pt0 dip hypo_depth mag rake ztor
===== ================================================================================== ================= ======================= ============================

Exposure model
--------------
=========== ==
#assets     14
#taxonomies 9 
=========== ==

======== ========== ======= ====== === === =========
taxonomy num_assets mean    stddev min max num_sites
RC_LR    3          1.00000 0%     1   1   3        
RC_MR    1          1.00000 nan    1   1   1        
RC_HR    1          1.00000 nan    1   1   1        
URM_1S   2          1.00000 0%     1   1   2        
URM_2S   2          1.00000 0%     1   1   2        
SAM_1S   1          1.00000 nan    1   1   1        
SAM_2S   2          1.00000 0%     1   1   2        
SAM_3S   1          1.00000 nan    1   1   1        
SAM_4S   1          1.00000 nan    1   1   1        
*ALL*    83         0.16867 240%   0   2   14       
======== ========== ======= ====== === === =========

Slowest sources
---------------
============ ==== ========= ========= ============
source_id    code calc_time num_sites eff_ruptures
============ ==== ========= ========= ============
AS_TRAS334   A    1.864E-04 6         760         
AS_TRAS346   A    1.624E-04 5         527         
AS_TRAS395   A    1.533E-04 3         432         
AS_TRAS458   A    1.483E-04 2         399         
AS_TRAS360   A    1.459E-04 3         624         
AS_TRAS410   A    1.440E-04 2         240         
FSBG_TRBG989 A    1.428E-04 1         108         
============ ==== ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
A    0.00108  
P    0.0      
==== =========

Information about the tasks
---------------------------
================== ====== ========= ====== ========= =========
operation-duration counts mean      stddev min       max      
preclassical       8      6.373E-04 4%     6.015E-04 6.709E-04
read_source_model  3      0.00441   78%    0.00146   0.00929  
================== ====== ========= ====== ========= =========

Data transfer
-------------
================= ================================ ========
task              sent                             received
read_source_model converter=996 B fname=332 B      8.83 KB 
preclassical      srcs=18.57 KB srcfilter=16.91 KB 1.89 KB 
================= ================================ ========

Slowest operations
------------------
========================= ======== ========= ======
calc_47305, maxmem=1.4 GB time_sec memory_mb counts
========================= ======== ========= ======
importing inputs          1.23338  0.0       1     
composite source model    1.17521  0.0       1     
total read_source_model   0.01323  0.72656   3     
total preclassical        0.00510  0.42578   8     
reading exposure          0.00230  0.0       1     
========================= ======== ========= ======