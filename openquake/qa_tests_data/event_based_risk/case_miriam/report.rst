Virtual Island - City C, 2 SES, grid=0.1
========================================

=============================================== ========================
tstation.gem.lan:/mnt/ssd/oqdata/calc_7589.hdf5 Wed Apr 26 15:54:46 2017
engine_version                                  2.4.0-git9336bd0        
hazardlib_version                               0.24.0-gita895d4c       
=============================================== ========================

num_sites = 281, sitecol = 97.5 KB

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
random_seed                     1024              
master_seed                     100               
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
========= ====== ====================================== =============== ================
smlt_path weight source_model_file                      gsim_logic_tree num_realizations
========= ====== ====================================== =============== ================
b1        1.000  `source_model.xml <source_model.xml>`_ trivial(1,1)    1/1             
========= ====== ====================================== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ========================= ========= ========== ==============
grp_id gsims                     distances siteparams ruptparams    
====== ========================= ========= ========== ==============
0      AkkarBommer2010()         rjb       vs30       rake mag      
1      AtkinsonBoore2003SInter() rrup      vs30       hypo_depth mag
====== ========================= ========= ========== ==============

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=2, rlzs=1)
  0,AkkarBommer2010(): ['<0,b1~b1_b6,w=1.0>']
  1,AtkinsonBoore2003SInter(): ['<0,b1~b1_b6,w=1.0>']>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== =========== ============ ============
source_model     grp_id trt                  num_sources eff_ruptures tot_ruptures
================ ====== ==================== =========== ============ ============
source_model.xml 0      Active Shallow Crust 1           41           2,558       
source_model.xml 1      Subduction Interface 1           382          3,945       
================ ====== ==================== =========== ============ ============

============= ======
#TRT models   2     
#sources      2     
#eff_ruptures 423   
#tot_ruptures 6,503 
#tot_weight   26,012
============= ======

Informational data
------------------
============================ ==================================================================================
compute_ruptures.received    tot 403.77 KB, max_per_task 45.14 KB                                              
compute_ruptures.sent        src_filter 1.62 MB, sources 65.3 KB, monitor 38.5 KB, gsims 3.23 KB, param 2.03 KB
hazard.input_weight          26,012                                                                            
hazard.n_imts                1 B                                                                               
hazard.n_levels              50 B                                                                              
hazard.n_realizations        1 B                                                                               
hazard.n_sites               281 B                                                                             
hazard.n_sources             2 B                                                                               
hazard.output_weight         14,050                                                                            
hostname                     tstation.gem.lan                                                                  
require_epsilons             1 B                                                                               
============================ ==================================================================================

Estimated data transfer for the avglosses
-----------------------------------------
548 asset(s) x 1 realization(s) x 1 loss type(s) x 1 losses x 8 bytes x 50 tasks = 214.06 KB

Exposure model
--------------
=============== ========
#assets         548     
#taxonomies     11      
deductibile     absolute
insurance_limit absolute
=============== ========

========== ===== ====== === === ========= ==========
taxonomy   mean  stddev min max num_sites num_assets
A-SPSB-1   1.250 0.463  1   2   8         10        
MC-RCSB-1  1.286 0.561  1   3   21        27        
MC-RLSB-2  1.256 0.880  1   6   39        49        
MR-RCSB-2  1.456 0.799  1   6   171       249       
MR-SLSB-1  1.000 0.0    1   1   5         5         
MS-FLSB-2  1.250 0.452  1   2   12        15        
MS-SLSB-1  1.545 0.934  1   4   11        17        
PCR-RCSM-5 1.000 0.0    1   1   2         2         
PCR-SLSB-1 1.000 0.0    1   1   3         3         
W-FLFB-2   1.222 0.502  1   3   54        66        
W-SLFB-1   1.265 0.520  1   3   83        105       
*ALL*      0.306 0.877  0   10  1,792     548       
========== ===== ====== === === ========= ==========

Slowest sources
---------------
====== ========= ================== ============ ========= ========= =========
grp_id source_id source_class       num_ruptures calc_time num_sites num_split
====== ========= ================== ============ ========= ========= =========
0      F         ComplexFaultSource 2,558        0.0       281       0        
1      D         ComplexFaultSource 3,945        0.0       281       0        
====== ========= ================== ============ ========= ========= =========

Computation times by source typology
------------------------------------
================== ========= ======
source_class       calc_time counts
================== ========= ======
ComplexFaultSource 0.0       2     
================== ========= ======

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
compute_ruptures   0.340 0.108  0.180 0.742 32       
================== ===== ====== ===== ===== =========

Slowest operations
------------------
================================ ========= ========= ======
operation                        time_sec  memory_mb counts
================================ ========= ========= ======
total compute_ruptures           10        1.098     32    
assoc_assets_sites               1.360     0.0       1     
filtering ruptures               0.393     0.0       489   
reading site collection          0.155     0.0       1     
reading composite source model   0.133     0.0       1     
saving ruptures                  0.089     0.0       32    
reading exposure                 0.059     0.0       1     
setting event years              0.014     0.0       1     
building site collection         0.009     0.0       1     
filtering composite source model 0.002     0.0       1     
store source_info                0.001     0.0       1     
managing sources                 9.584E-05 0.0       1     
================================ ========= ========= ======