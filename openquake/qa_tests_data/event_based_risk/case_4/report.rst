Event Based Risk for Turkey reduced
===================================

============== ===================
checksum32     4_007_884_407      
date           2020-03-13T11:21:44
engine_version 3.9.0-gitfb3ef3a732
============== ===================

num_sites = 13, num_levels = 60, num_rlzs = 12

Parameters
----------
=============================== ==================
calculation_mode                'preclassical'    
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              10.0              
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            4.0               
complex_fault_mesh_spacing      4.0               
width_of_mfd_bin                0.1               
area_source_discretization      20.0              
pointsource_distance            {'default': 0}    
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     323               
master_seed                     42                
ses_seed                        323               
=============================== ==================

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
======================== ======= ================
smlt_path                weight  num_realizations
======================== ======= ================
AreaSource               0.50000 4               
FaultSourceAndBackground 0.20000 4               
SeiFaCrust               0.30000 4               
======================== ======= ================

Required parameters per tectonic region type
--------------------------------------------
====== ================================================================================== ================= ======================= ============================
grp_id gsims                                                                              distances         siteparams              ruptparams                  
====== ================================================================================== ================= ======================= ============================
0      '[AkkarBommer2010]' '[CauzziFaccioli2008]' '[ChiouYoungs2008]' '[ZhaoEtAl2006Asc]' rhypo rjb rrup rx vs30 vs30measured z1pt0 dip hypo_depth mag rake ztor
1      '[AkkarBommer2010]' '[CauzziFaccioli2008]' '[ChiouYoungs2008]' '[ZhaoEtAl2006Asc]' rhypo rjb rrup rx vs30 vs30measured z1pt0 dip hypo_depth mag rake ztor
2      '[AkkarBommer2010]' '[CauzziFaccioli2008]' '[ChiouYoungs2008]' '[ZhaoEtAl2006Asc]' rhypo rjb rrup rx vs30 vs30measured z1pt0 dip hypo_depth mag rake ztor
====== ================================================================================== ================= ======================= ============================

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      0.21697   2_982        2_982       
1      0.11111   108          54          
2      NaN       9            0.0         
====== ========= ============ ============

Exposure model
--------------
=========== ==
#assets     14
#taxonomies 9 
=========== ==

======== ======= ======= === === ========= ==========
taxonomy mean    stddev  min max num_sites num_assets
RC_LR    1.00000 0.0     1   1   3         3         
RC_MR    1.00000 NaN     1   1   1         1         
RC_HR    1.00000 NaN     1   1   1         1         
URM_1S   1.00000 0.0     1   1   2         2         
URM_2S   1.00000 0.0     1   1   2         2         
SAM_1S   1.00000 NaN     1   1   1         1         
SAM_2S   1.00000 0.0     1   1   2         2         
SAM_3S   1.00000 NaN     1   1   1         1         
SAM_4S   1.00000 NaN     1   1   1         1         
*ALL*    0.16867 0.40783 0   2   83        14        
======== ======= ======= === === ========= ==========

Slowest sources
---------------
============ ====== ==== ============ ========= ========= ============
source_id    grp_id code num_ruptures calc_time num_sites eff_ruptures
============ ====== ==== ============ ========= ========= ============
AS_TRAS360   0      A    624          0.00531   0.14904   624         
AS_TRAS334   0      A    760          0.00530   0.31316   760         
AS_TRAS346   0      A    527          0.00473   0.23340   527         
AS_TRAS395   0      A    432          0.00430   0.18750   432         
AS_TRAS458   0      A    399          0.00373   0.10526   399         
AS_TRAS410   0      A    240          0.00290   0.29167   240         
FSBG_TRBG989 1      A    108          0.00221   0.11111   54          
============ ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
A    0.02848  
P    0.0      
==== =========

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
preclassical       0.01256 0.00655 0.00250 0.02215 8      
read_source_model  0.03236 0.04160 0.00304 0.07997 3      
================== ======= ======= ======= ======= =======

Data transfer
-------------
================= ========================================== ========
task              sent                                       received
read_source_model converter=996 B fname=332 B srcfilter=12 B 12.17 KB
preclassical      srcs=18.24 KB params=9.13 KB gsims=3.8 KB  2.84 KB 
================= ========================================== ========

Slowest operations
------------------
=========================== ======== ========= ======
calc_66955                  time_sec memory_mb counts
=========================== ======== ========= ======
composite source model      0.14046  0.12500   1     
total preclassical          0.10046  1.85547   8     
total read_source_model     0.09707  0.0       3     
splitting/filtering sources 0.06404  0.0       8     
reading exposure            0.00236  0.0       1     
aggregate curves            0.00218  0.0       7     
store source_info           0.00217  0.0       1     
=========================== ======== ========= ======