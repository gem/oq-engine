Event Based Risk for Turkey reduced
===================================

============== ===================
checksum32     39,734,555         
date           2019-10-02T10:07:21
engine_version 3.8.0-git6f03622c6e
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
0      21        2,982        10          
1      1.00000   108          2.00000     
2      0.0       9            0.0         
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
AS_TRAS334   0      A    760          0.02976   3.00000   2.00000     
AS_TRAS458   0      A    399          0.02178   1.00000   2.00000     
AS_TRAS346   0      A    527          0.01948   2.50000   2.00000     
AS_TRAS360   0      A    624          0.01563   1.50000   2.00000     
AS_TRAS395   0      A    432          0.01344   1.50000   2.00000     
FSBG_TRBG989 1      A    108          0.00558   0.50000   2.00000     
============ ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
A    0.11110   7     
P    0.0       1     
==== ========= ======

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
SourceReader       0.02963 0.03999 0.00115 0.07535 3      
compute_gmfs       0.02092 0.00489 0.01575 0.03927 29     
sample_ruptures    0.01695 0.01054 0.00283 0.03433 8      
================== ======= ======= ======= ======= =======

Data transfer
-------------
=============== ==================================================== =========
task            sent                                                 received 
SourceReader    apply_unc=4.68 KB ltmodel=610 B fname=353 B          23.78 KB 
compute_gmfs    param=209.94 KB rupgetter=52.96 KB srcfilter=6.32 KB 219.57 KB
sample_ruptures param=56.98 KB sources=17.12 KB srcfilter=1.74 KB    9.92 KB  
=============== ==================================================== =========

Slowest operations
------------------
======================== ======== ========= ======
calc_29490               time_sec memory_mb counts
======================== ======== ========= ======
EventBasedCalculator.run 0.90400  0.89453   1     
total compute_gmfs       0.60682  1.36719   29    
building hazard          0.29565  0.37891   29    
getting ruptures         0.19803  1.05469   29    
total sample_ruptures    0.13557  0.22266   8     
composite source model   0.10040  1.03125   1     
total SourceReader       0.08889  0.0       3     
saving events            0.08053  0.0       1     
saving gmfs              0.04326  0.0       29    
building hazard curves   0.03425  0.0       236   
saving ruptures          0.01353  0.0       6     
aggregating hcurves      0.00989  0.0       29    
saving gmf_data/indices  0.00898  0.0       1     
store source_info        0.00270  0.0       1     
reading exposure         0.00207  0.0       1     
======================== ======== ========= ======