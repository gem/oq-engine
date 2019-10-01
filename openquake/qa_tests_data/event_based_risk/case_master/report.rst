event based risk
================

============== ===================
checksum32     1,634,090,954      
date           2019-10-01T06:09:03
engine_version 3.8.0-gite0871b5c35
============== ===================

num_sites = 7, num_levels = 46, num_rlzs = 8

Parameters
----------
=============================== ==================
calculation_mode                'event_based_risk'
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              1.0               
ses_per_logic_tree_path         10                
truncation_level                3.0               
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                0.1               
area_source_discretization      10.0              
ground_motion_correlation_model 'JB2009'          
minimum_intensity               {}                
random_seed                     24                
master_seed                     0                 
ses_seed                        42                
avg_losses                      True              
=============================== ==================

Input files
-----------
=================================== ================================================================================
Name                                File                                                                            
=================================== ================================================================================
business_interruption_vulnerability `downtime_vulnerability_model.xml <downtime_vulnerability_model.xml>`_          
contents_vulnerability              `contents_vulnerability_model.xml <contents_vulnerability_model.xml>`_          
exposure                            `exposure_model.xml <exposure_model.xml>`_                                      
gsim_logic_tree                     `gsim_logic_tree.xml <gsim_logic_tree.xml>`_                                    
job_ini                             `job.ini <job.ini>`_                                                            
nonstructural_vulnerability         `nonstructural_vulnerability_model.xml <nonstructural_vulnerability_model.xml>`_
occupants_vulnerability             `occupants_vulnerability_model.xml <occupants_vulnerability_model.xml>`_        
source_model_logic_tree             `ssmLT.xml <ssmLT.xml>`_                                                        
structural_vulnerability            `structural_vulnerability_model.xml <structural_vulnerability_model.xml>`_      
=================================== ================================================================================

Composite source model
----------------------
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
b1        0.25000 complex(2,0,2)  4               
b2        0.75000 complex(2,0,2)  4               
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ============================================================== =========== ======================= =================
grp_id gsims                                                          distances   siteparams              ruptparams       
====== ============================================================== =========== ======================= =================
0      '[BooreAtkinson2008]' '[ChiouYoungs2008]'                      rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
1      '[AkkarBommer2010]\nminimum_distance = 10' '[ChiouYoungs2008]' rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
2      '[BooreAtkinson2008]' '[ChiouYoungs2008]'                      rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
3      '[AkkarBommer2010]\nminimum_distance = 10' '[ChiouYoungs2008]' rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
====== ============================================================== =========== ======================= =================

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=16, rlzs=8)>

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      7.00000   482          0.0         
1      7.00000   4            2.00000     
2      7.00000   482          0.0         
3      7.00000   1            0.0         
====== ========= ============ ============

Estimated data transfer for the avglosses
-----------------------------------------
7 asset(s) x 8 realization(s) x 5 loss type(s) losses x 8 bytes x 8 tasks = 17.5 KB

Exposure model
--------------
=========== =
#assets     7
#taxonomies 3
=========== =

======== ======= ====== === === ========= ==========
taxonomy mean    stddev min max num_sites num_assets
tax1     1.00000 0.0    1   1   4         4         
tax2     1.00000 0.0    1   1   2         2         
tax3     1.00000 NaN    1   1   1         1         
*ALL*    1.00000 0.0    1   1   7         7         
======== ======= ====== === === ========= ==========

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============ =====
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures speed
========= ====== ==== ============ ========= ========= ============ =====
1         2      S    482          0.08728   7.00000   0.0          0.0  
1         0      S    482          0.08291   7.00000   0.0          0.0  
2         1      S    4            0.00483   7.00000   2.00000      413  
2         3      X    1            3.130E-04 7.00000   0.0          0.0  
========= ====== ==== ============ ========= ========= ============ =====

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
S    0.17503   3     
X    3.130E-04 1     
==== ========= ======

Duplicated sources
------------------
Found 2 unique sources and 1 duplicate sources with multiplicity 2.0: ['1']

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
SourceReader       0.01996 0.01118 0.01205 0.02787 2      
compute_gmfs       0.04578 0.00246 0.04355 0.04842 3      
sample_ruptures    0.04827 0.04826 0.00245 0.09213 4      
================== ======= ======= ======= ======= =======

Data transfer
-------------
=============== ================================================ ========
task            sent                                             received
SourceReader    apply_unc=2.4 KB ltmodel=378 B fname=220 B       17.23 KB
compute_gmfs    param=16.31 KB rupgetter=4.72 KB srcfilter=669 B 55.07 KB
sample_ruptures param=21.61 KB sources=14.04 KB srcfilter=892 B  2.3 KB  
=============== ================================================ ========

Slowest operations
------------------
======================== ========= ========= ======
calc_23210               time_sec  memory_mb counts
======================== ========= ========= ======
EventBasedCalculator.run 0.39618   1.32422   1     
total sample_ruptures    0.19309   0.0       4     
total compute_gmfs       0.13735   0.64453   3     
building hazard          0.06052   0.0       3     
composite source model   0.04746   0.25391   1     
total SourceReader       0.03992   0.0       2     
building hazard curves   0.03767   0.0       80    
getting ruptures         0.02939   0.64453   3     
saving events            0.01228   0.0       1     
saving gmf_data/indices  0.00786   0.0       1     
saving gmfs              0.00534   0.0       3     
aggregating hcurves      0.00242   0.0       3     
saving ruptures          0.00242   0.0       1     
store source_info        0.00210   0.0       1     
reading exposure         6.316E-04 0.0       1     
======================== ========= ========= ======