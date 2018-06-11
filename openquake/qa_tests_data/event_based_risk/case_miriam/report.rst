Virtual Island - City C, 2 SES, grid=0.1
========================================

============== ===================
checksum32     604,091,143        
date           2018-06-05T06:38:38
engine_version 3.2.0-git65c4735   
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
source_model.xml 0      Active Shallow Crust 2,558        2,558       
source_model.xml 1      Subduction Interface 3,945        3,945       
================ ====== ==================== ============ ============

============= =====
#TRT models   2    
#eff_ruptures 6,503
#tot_ruptures 6,503
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
D         ComplexFaultSource 3,945        8.92168   4.189E-04  1,792     47        2,054 
F         ComplexFaultSource 2,558        5.39641   3.607E-04  1,792     35        250   
========= ================== ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
================== ========= ======
source_class       calc_time counts
================== ========= ======
ComplexFaultSource 14        2     
================== ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =========
operation-duration mean    stddev  min     max     num_tasks
RtreeFilter        0.01803 0.00974 0.00786 0.04244 41       
compute_ruptures   1.44569 0.63156 0.19824 2.32474 10       
================== ======= ======= ======= ======= =========

Data transfer
-------------
================ ============================================================================== =========
task             sent                                                                           received 
RtreeFilter      srcs=82.43 KB monitor=13.85 KB srcfilter=11.17 KB                              659.52 KB
compute_ruptures sources=643.07 KB param=9.6 KB monitor=3.45 KB src_filter=2.28 KB gsims=1.3 KB 15.3 MB  
================ ============================================================================== =========

Slowest operations
------------------
=============================== ======== ========= ======
operation                       time_sec memory_mb counts
=============================== ======== ========= ======
total compute_ruptures          14       17        10    
EventBasedRuptureCalculator.run 3.48851  13        1     
managing sources                2.65927  13        1     
total prefilter                 0.73928  4.75391   41    
reading site collection         0.36316  0.30078   1     
reading composite source model  0.24262  0.0       1     
making contexts                 0.14567  0.0       489   
saving ruptures                 0.06078  1.02344   10    
reading exposure                0.05565  0.0       1     
unpickling compute_ruptures     0.03523  3.36719   10    
unpickling prefilter            0.01498  0.0       41    
store source_info               0.00801  0.0       1     
setting event years             0.00374  0.0       1     
splitting sources               0.00107  0.0       1     
=============================== ======== ========= ======