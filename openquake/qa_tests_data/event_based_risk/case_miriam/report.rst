Virtual Island - City C, 2 SES, grid=0.1
========================================

============================================== ========================
gem-tstation:/home/michele/ssd/calc_81051.hdf5 Thu Jan 26 14:28:43 2017
engine_version                                 2.3.0-gite807292        
hazardlib_version                              0.23.0-gite1ea7ea       
============================================== ========================

num_sites = 281, sitecol = 83.46 KB

Parameters
----------
=============================== ==============================================================
calculation_mode                'event_based_risk'                                            
number_of_logic_tree_samples    0                                                             
maximum_distance                {'Active Shallow Crust': 200.0, 'Subduction Interface': 200.0}
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
=============================== ==============================================================

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
b1        1.000  `source_model.xml <source_model.xml>`_ trivial(1,0)    1/1             
========= ====== ====================================== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================= ========= ========== ==========
grp_id gsims             distances siteparams ruptparams
====== ================= ========= ========== ==========
0      AkkarBommer2010() rjb       vs30       mag rake  
====== ================= ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)
  0,AkkarBommer2010(): ['<0,b1~b1_@,w=1.0>']>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== =========== ============ ============
source_model     grp_id trt                  num_sources eff_ruptures tot_ruptures
================ ====== ==================== =========== ============ ============
source_model.xml 0      Active Shallow Crust 1           44           2,558       
================ ====== ==================== =========== ============ ============

Informational data
------------------
========================================= ============
compute_ruptures_max_received_per_task    13,147      
compute_ruptures_num_tasks                15          
compute_ruptures_sent.gsims               1,470       
compute_ruptures_sent.monitor             21,090      
compute_ruptures_sent.sources             30,514      
compute_ruptures_sent.src_filter          582,465     
compute_ruptures_tot_received             100,226     
hazard.input_weight                       10,232      
hazard.n_imts                             1           
hazard.n_levels                           50          
hazard.n_realizations                     1           
hazard.n_sites                            281         
hazard.n_sources                          1           
hazard.output_weight                      14,050      
hostname                                  gem-tstation
require_epsilons                          1           
========================================= ============

Specific information for event based
------------------------------------
======================== =====
Total number of ruptures 44   
Total number of events   45   
Rupture multiplicity     1.023
======================== =====

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
*ALL*      1.950 1.306  1   10  281       548       
========== ===== ====== === === ========= ==========

Slowest sources
---------------
====== ========= ================== ============ ========= ========= =========
grp_id source_id source_class       num_ruptures calc_time num_sites num_split
====== ========= ================== ============ ========= ========= =========
0      F         ComplexFaultSource 2,558        0.0       281       0        
====== ========= ================== ============ ========= ========= =========

Computation times by source typology
------------------------------------
================== ========= ======
source_class       calc_time counts
================== ========= ======
ComplexFaultSource 0.0       1     
================== ========= ======

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
compute_ruptures   0.270 0.038  0.192 0.366 15       
================== ===== ====== ===== ===== =========

Slowest operations
------------------
================================ ========= ========= ======
operation                        time_sec  memory_mb counts
================================ ========= ========= ======
total compute_ruptures           4.049     1.281     15    
managing sources                 0.603     0.0       1     
split/filter heavy sources       0.600     0.0       1     
reading site collection          0.199     0.0       1     
reading composite source model   0.111     0.0       1     
reading exposure                 0.082     0.0       1     
saving ruptures                  0.015     0.0       15    
filtering ruptures               0.013     0.0       57    
setting event years              0.002     0.0       1     
filtering composite source model 0.002     0.0       1     
store source_info                5.314E-04 0.0       1     
================================ ========= ========= ======