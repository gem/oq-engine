Virtual Island - City C, 2 SES, grid=0.1
========================================

============== ===================
checksum32     268,415,131        
date           2018-09-05T10:04:23
engine_version 3.2.0-gitb4ef3a4b6c
============== ===================

num_sites = 1792, num_levels = 50

Parameters
----------
=============================== ==================
calculation_mode                'event_based_risk'
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              50.0              
ses_per_logic_tree_path         2                 
truncation_level                4.0               
rupture_mesh_spacing            10.0              
complex_fault_mesh_spacing      10.0              
width_of_mfd_bin                0.2               
area_source_discretization      None              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     1024              
master_seed                     100               
ses_seed                        42                
avg_losses                      True              
=============================== ==================

Input files
-----------
======================== ============================================================
Name                     File                                                        
======================== ============================================================
exposure                 `exposure_model.xml <exposure_model.xml>`_                  
gsim_logic_tree          `gsim_logic_tree.xml <gsim_logic_tree.xml>`_                
job_ini                  `job.ini <job.ini>`_                                        
source                   `source_model.xml <source_model.xml>`_                      
source_model_logic_tree  `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
structural_vulnerability `vulnerability_model.xml <vulnerability_model.xml>`_        
======================== ============================================================

Composite source model
----------------------
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
b1        1.00000 trivial(1,1)    1/1             
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ========================= ========= ========== ==============
grp_id gsims                     distances siteparams ruptparams    
====== ========================= ========= ========== ==============
0      AkkarBommer2010()         rjb       vs30       mag rake      
1      AtkinsonBoore2003SInter() rrup      vs30       hypo_depth mag
====== ========================= ========= ========== ==============

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=2, rlzs=1)
  0,AkkarBommer2010(): [0]
  1,AtkinsonBoore2003SInter(): [0]>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== ============ ============
source_model     grp_id trt                  eff_ruptures tot_ruptures
================ ====== ==================== ============ ============
source_model.xml 0      Active Shallow Crust 2,348        2,348       
source_model.xml 1      Subduction Interface 3,645        3,645       
================ ====== ==================== ============ ============

============= =====
#TRT models   2    
#eff_ruptures 5,993
#tot_ruptures 5,993
#tot_weight   0    
============= =====

Estimated data transfer for the avglosses
-----------------------------------------
548 asset(s) x 1 realization(s) x 1 loss type(s) x 1 losses x 8 bytes x 8 tasks = 34.25 KB

Exposure model
--------------
=============== ========
#assets         548     
#taxonomies     11      
deductibile     absolute
insurance_limit absolute
=============== ========

========== ======= ======= === === ========= ==========
taxonomy   mean    stddev  min max num_sites num_assets
MS-FLSB-2  1.25000 0.45227 1   2   12        15        
MS-SLSB-1  1.54545 0.93420 1   4   11        17        
MC-RLSB-2  1.25641 0.88013 1   6   39        49        
W-SLFB-1   1.26506 0.51995 1   3   83        105       
MR-RCSB-2  1.45614 0.79861 1   6   171       249       
MC-RCSB-1  1.28571 0.56061 1   3   21        27        
W-FLFB-2   1.22222 0.50157 1   3   54        66        
PCR-RCSM-5 1.00000 0.0     1   1   2         2         
MR-SLSB-1  1.00000 0.0     1   1   5         5         
A-SPSB-1   1.25000 0.46291 1   2   8         10        
PCR-SLSB-1 1.00000 0.0     1   1   3         3         
*ALL*      0.30580 0.87729 0   10  1,792     548       
========== ======= ======= === === ========= ==========

Slowest sources
---------------
========= ================== ============ ========= ========== ========= ========= ======
source_id source_class       num_ruptures calc_time split_time num_sites num_split events
========= ================== ============ ========= ========== ========= ========= ======
D         ComplexFaultSource 3,645        7.64620   4.663E-04  1,792     44        329   
F         ComplexFaultSource 2,348        4.35809   3.793E-04  1,792     32        30    
========= ================== ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
================== ========= ======
source_class       calc_time counts
================== ========= ======
ComplexFaultSource 12        2     
================== ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
==================== ======= ========= ======= ======= =========
operation-duration   mean    stddev    min     max     num_tasks
pickle_source_models 0.20885 NaN       0.20885 0.20885 1        
preprocess           1.24713 0.33345   0.80785 2.08284 10       
compute_gmfs         0.00671 4.564E-04 0.00601 0.00728 5        
==================== ======= ========= ======= ======= =========

Data transfer
-------------
==================== =================================================================================================== ========
task                 sent                                                                                                received
pickle_source_models monitor=0 B fnames=0 B converter=0 B                                                                167 B   
preprocess           srcs=45.83 KB param=4.13 KB monitor=3.49 KB srcfilter=2.47 KB                                       13 MB   
compute_gmfs         sources_or_ruptures=12.83 MB param=23.85 KB monitor=1.68 KB rlzs_by_gsim=1.49 KB src_filter=1.07 KB 12.43 MB
==================== =================================================================================================== ========

Slowest operations
------------------
========================== ======== ========= ======
operation                  time_sec memory_mb counts
========================== ======== ========= ======
total preprocess           12       9.37500   10    
saving ruptures            0.21677  0.85156   53    
total pickle_source_models 0.20903  0.0       3     
making contexts            0.11890  0.0       394   
reading exposure           0.04472  0.0       1     
total compute_gmfs         0.03353  5.34375   5     
managing sources           0.02713  15        1     
building ruptures          0.01819  5.26953   5     
GmfGetter.init             0.01100  0.01172   5     
aggregating hcurves        0.00492  0.0       5     
store source_info          0.00446  0.07031   1     
setting event years        0.00210  0.0       1     
splitting sources          0.00119  0.0       1     
========================== ======== ========= ======