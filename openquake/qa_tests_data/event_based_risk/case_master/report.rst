event based risk
================

============== ===================
checksum32     1,634,090,954      
date           2019-07-30T15:04:37
engine_version 3.7.0-git3b3dff46da
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

Number of ruptures per tectonic region type
-------------------------------------------
================== ====== ==================== ============ ============
source_model       grp_id trt                  eff_ruptures tot_ruptures
================== ====== ==================== ============ ============
source_model_1.xml 0      Active Shallow Crust 1            482         
source_model_1.xml 1      Stable Shallow Crust 1            4           
source_model_2.xml 2      Active Shallow Crust 1            482         
source_model_2.xml 3      Stable Shallow Crust 1            1           
================== ====== ==================== ============ ============

============= ===
#TRT models   4  
#eff_ruptures 4  
#tot_ruptures 969
============= ===

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
========= ====== ==== ============ ========= ========= ======= =====
source_id grp_id code num_ruptures calc_time num_sites weight  speed
========= ====== ==== ============ ========= ========= ======= =====
1         0      S    482          0.18052   14        0.0     0.0  
2         1      S    4            0.00205   14        2.00000 973  
========= ====== ==== ============ ========= ========= ======= =====

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
S    0.18257   3     
X    0.0       1     
==== ========= ======

Duplicated sources
------------------
Found 2 unique sources and 1 duplicate sources with multiplicity 2.0: ['1']

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
compute_gmfs       0.03660 0.00474 0.03199 0.04147 3      
read_source_models 0.01275 0.00917 0.00627 0.01923 2      
sample_ruptures    0.05132 0.05477 0.00235 0.09901 4      
================== ======= ======= ======= ======= =======

Data transfer
-------------
================== ================================================ ========
task               sent                                             received
compute_gmfs       param=15.86 KB rupgetter=4.96 KB srcfilter=660 B 56.11 KB
read_source_models converter=628 B fnames=226 B                     13.93 KB
sample_ruptures    param=21.61 KB sources=14.08 KB srcfilter=880 B  2.27 KB 
================== ================================================ ========

Slowest operations
------------------
======================== ========= ========= ======
calc_15567               time_sec  memory_mb counts
======================== ========= ========= ======
EventBasedCalculator.run 0.51697   1.60547   1     
total sample_ruptures    0.20529   0.0       4     
total compute_gmfs       0.10981   0.22266   3     
building hazard          0.04925   0.22266   3     
building hazard curves   0.03003   0.0       80    
total read_source_models 0.02551   0.0       2     
getting ruptures         0.02075   0.0       3     
saving gmfs              0.01174   0.0       3     
saving events            0.01057   0.06250   1     
saving gmf_data/indices  0.00838   0.0       1     
saving ruptures          0.00513   0.0       1     
aggregating hcurves      0.00445   0.0       3     
store source_info        0.00223   0.0       1     
reading exposure         7.472E-04 0.0       1     
GmfGetter.init           4.823E-04 0.0       3     
======================== ========= ========= ======