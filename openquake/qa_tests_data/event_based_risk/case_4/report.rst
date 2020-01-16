Event Based Risk for Turkey reduced
===================================

============== ===================
checksum32     3_359_983_435      
date           2020-01-16T05:31:05
engine_version 3.8.0-git83c45f7244
============== ===================

num_sites = 13, num_levels = 91, num_rlzs = 8

Parameters
----------
=============================== ==================
calculation_mode                'event_based_risk'
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
avg_losses                      True              
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
======================== ======= ====================== ================
smlt_path                weight  gsim_logic_tree        num_realizations
======================== ======= ====================== ================
AreaSource               0.50000 simple(4,0,0,0,0,0,0)  4               
FaultSourceAndBackground 0.20000 simple(4,0,0,0,0,0,0)  4               
SeiFaCrust               0.30000 trivial(0,0,0,0,0,0,0) 0               
======================== ======= ====================== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================================================================================== ================= ======================= ============================
grp_id gsims                                                                              distances         siteparams              ruptparams                  
====== ================================================================================== ================= ======================= ============================
0      '[AkkarBommer2010]' '[CauzziFaccioli2008]' '[ChiouYoungs2008]' '[ZhaoEtAl2006Asc]' rhypo rjb rrup rx vs30 vs30measured z1pt0 dip hypo_depth mag rake ztor
1      '[AkkarBommer2010]' '[CauzziFaccioli2008]' '[ChiouYoungs2008]' '[ZhaoEtAl2006Asc]' rhypo rjb rrup rx vs30 vs30measured z1pt0 dip hypo_depth mag rake ztor
2      '[AkkarBommer2010]' '[CauzziFaccioli2008]' '[ChiouYoungs2008]' '[ZhaoEtAl2006Asc]' rhypo rjb rrup rx vs30 vs30measured z1pt0 dip hypo_depth mag rake ztor
====== ================================================================================== ================= ======================= ============================

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=32, rlzs=8)>

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      2.10000   2_982        10          
1      0.50000   108          2.00000     
2      NaN       9            0.0         
====== ========= ============ ============

Estimated data transfer for the avglosses
-----------------------------------------
14 asset(s) x 8 realization(s) x 1 loss type(s) losses x 8 bytes x 64 tasks = 56 KB

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
AS_TRAS334   0      A    760          0.02219   3.00000   2.00000     
AS_TRAS346   0      A    527          0.02094   2.50000   2.00000     
AS_TRAS458   0      A    399          0.01913   1.00000   2.00000     
AS_TRAS360   0      A    624          0.01685   1.50000   2.00000     
AS_TRAS395   0      A    432          0.01305   1.50000   2.00000     
FSBG_TRBG989 1      A    108          0.00553   0.50000   2.00000     
============ ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
A    0.10504  
P    0.0      
==== =========

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
SourceReader       0.03028 0.03928 0.00284 0.07528 3      
compute_gmfs       0.03619 0.01129 0.01421 0.05358 12     
sample_ruptures    0.01680 0.00868 0.00311 0.02689 8      
================== ======= ======= ======= ======= =======

Data transfer
-------------
=============== ================================================= =========
task            sent                                              received 
SourceReader    apply_unc=4.68 KB ltmodel=610 B fname=353 B       16.02 KB 
sample_ruptures param=56.41 KB sources=17.23 KB srcfilter=1.74 KB 9.92 KB  
compute_gmfs    param=86 KB rupgetter=26.97 KB srcfilter=2.61 KB  110.79 KB
=============== ================================================= =========

Slowest operations
------------------
======================== ======== ========= ======
calc_43286               time_sec memory_mb counts
======================== ======== ========= ======
EventBasedCalculator.run 0.72986  1.53125   1     
total compute_gmfs       0.43431  1.58984   12    
total sample_ruptures    0.13440  0.53516   8     
composite source model   0.09922  0.0       1     
total SourceReader       0.09085  0.0       3     
saving events            0.07637  0.0       1     
getting ruptures         0.03605  0.0       29    
building hazard curves   0.01910  0.0       132   
saving ruptures          0.01141  0.0       6     
aggregating hcurves      0.00415  0.0       12    
store source_info        0.00238  0.0       1     
reading exposure         0.00179  0.0       1     
saving gmfs              0.00151  0.0       12    
======================== ======== ========= ======