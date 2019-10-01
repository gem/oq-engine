Event Based Risk for Turkey reduced
===================================

============== ===================
checksum32     39,734,555         
date           2019-10-01T07:00:59
engine_version 3.8.0-gitbd71c2f960
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
============ ====== ==== ============ ========= ========= ============ =====
source_id    grp_id code num_ruptures calc_time num_sites eff_ruptures speed
============ ====== ==== ============ ========= ========= ============ =====
AS_TRAS334   0      A    760          0.03069   6.00000   2.00000      65   
AS_TRAS458   0      A    399          0.02104   2.00000   2.00000      95   
AS_TRAS346   0      A    527          0.01947   5.00000   2.00000      102  
AS_TRAS360   0      A    624          0.01639   3.00000   2.00000      122  
AS_TRAS395   0      A    432          0.01301   3.00000   2.00000      153  
FSBG_TRBG989 1      A    108          0.00778   1.00000   2.00000      257  
AS_TRAS410   0      A    240          0.00397   2.00000   0.0          0.0  
============ ====== ==== ============ ========= ========= ============ =====

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
A    0.11236   7     
P    0.0       1     
==== ========= ======

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
SourceReader       0.02777 0.04061 0.00113 0.07450 3      
compute_gmfs       0.02017 0.00269 0.01420 0.02452 29     
sample_ruptures    0.01709 0.01080 0.00228 0.03546 8      
================== ======= ======= ======= ======= =======

Data transfer
-------------
=============== ==================================================== =========
task            sent                                                 received 
SourceReader    apply_unc=4.68 KB ltmodel=610 B fname=353 B          22.1 KB  
compute_gmfs    param=209.94 KB rupgetter=52.93 KB srcfilter=6.29 KB 219.57 KB
sample_ruptures param=56.98 KB sources=17.12 KB srcfilter=1.73 KB    9.92 KB  
=============== ==================================================== =========

Slowest operations
------------------
======================== ======== ========= ======
calc_6603                time_sec memory_mb counts
======================== ======== ========= ======
EventBasedCalculator.run 0.87901  0.74609   1     
total compute_gmfs       0.58501  1.45312   29    
building hazard          0.28493  0.25000   29    
getting ruptures         0.19066  1.20703   29    
total sample_ruptures    0.13673  0.29297   8     
composite source model   0.09718  0.51562   1     
total SourceReader       0.08330  0.0       3     
saving events            0.07709  0.0       1     
saving gmfs              0.04533  0.0       29    
building hazard curves   0.03200  0.0       236   
saving ruptures          0.01263  0.0       6     
aggregating hcurves      0.01000  0.0       29    
saving gmf_data/indices  0.00933  0.0       1     
store source_info        0.00239  0.0       1     
reading exposure         0.00170  0.0       1     
======================== ======== ========= ======