Event Based Risk Lisbon
=======================

============================================ ========================
gem-tstation:/mnt/ssd/oqdata/calc_85545.hdf5 Tue Feb 14 15:37:10 2017
engine_version                               2.3.0-git1f56df2        
hazardlib_version                            0.23.0-git6937706       
============================================ ========================

num_sites = 1, sitecol = 809 B

Parameters
----------
=============================== ==================
calculation_mode                'event_based_risk'
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 400.0}
investigation_time              2.0               
ses_per_logic_tree_path         1                 
truncation_level                5.0               
rupture_mesh_spacing            4.0               
complex_fault_mesh_spacing      4.0               
width_of_mfd_bin                0.1               
area_source_discretization      10.0              
ground_motion_correlation_model None              
random_seed                     23                
master_seed                     42                
avg_losses                      True              
=============================== ==================

Input files
-----------
======================== ============================================================
Name                     File                                                        
======================== ============================================================
exposure                 `exposure_model_1asset.xml <exposure_model_1asset.xml>`_    
gsim_logic_tree          `gsim_logic_tree.xml <gsim_logic_tree.xml>`_                
job_ini                  `job.ini <job.ini>`_                                        
source                   `SA_RA_CATAL1_00.xml <SA_RA_CATAL1_00.xml>`_                
source                   `SA_RA_CATAL2_00.xml <SA_RA_CATAL2_00.xml>`_                
source_model_logic_tree  `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
structural_vulnerability `vulnerability_model2013.xml <vulnerability_model2013.xml>`_
======================== ============================================================

Composite source model
----------------------
========= ====== ============================================ =============== ================
smlt_path weight source_model_file                            gsim_logic_tree num_realizations
========= ====== ============================================ =============== ================
b1        0.600  `SA_RA_CATAL1_00.xml <SA_RA_CATAL1_00.xml>`_ complex(2,2)    2/2             
b2        0.400  `SA_RA_CATAL2_00.xml <SA_RA_CATAL2_00.xml>`_ complex(2,2)    4/4             
========= ====== ============================================ =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ===================================== ========= ========== ==========
grp_id gsims                                 distances siteparams ruptparams
====== ===================================== ========= ========== ==========
0      AkkarBommer2010() AtkinsonBoore2006() rrup rjb  vs30       mag rake  
2      AkkarBommer2010() AtkinsonBoore2006() rrup rjb  vs30       mag rake  
3      AkkarBommer2010() AtkinsonBoore2006() rrup rjb  vs30       mag rake  
====== ===================================== ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=6, rlzs=6)
  0,AkkarBommer2010(): ['<1,b1~b2_@,w=0.1800000017881393>']
  0,AtkinsonBoore2006(): ['<0,b1~b1_@,w=0.420000004172325>']
  2,AkkarBommer2010(): ['<4,b2~b2_b3,w=0.0839999987483025>', '<5,b2~b2_b4,w=0.03599999946355822>']
  2,AtkinsonBoore2006(): ['<2,b2~b1_b3,w=0.1959999970793725>', '<3,b2~b1_b4,w=0.0839999987483025>']
  3,AkkarBommer2010(): ['<3,b2~b1_b4,w=0.0839999987483025>', '<5,b2~b2_b4,w=0.03599999946355822>']
  3,AtkinsonBoore2006(): ['<2,b2~b1_b3,w=0.1959999970793725>', '<4,b2~b2_b3,w=0.0839999987483025>']>

Number of ruptures per tectonic region type
-------------------------------------------
=================== ====== ==================== =========== ============ ============
source_model        grp_id trt                  num_sources eff_ruptures tot_ruptures
=================== ====== ==================== =========== ============ ============
SA_RA_CATAL1_00.xml 0      Active Shallow Crust 3           4            48,521      
SA_RA_CATAL2_00.xml 2      Active Shallow Crust 3           6            48,521      
SA_RA_CATAL2_00.xml 3      Stable Shallow Crust 8           3            21,381      
=================== ====== ==================== =========== ============ ============

============= =======
#TRT models   3      
#sources      14     
#eff_ruptures 13     
#tot_ruptures 118,423
#tot_weight   13,980 
============= =======

Informational data
------------------
========================================= ============
compute_ruptures_max_received_per_task    7,740       
compute_ruptures_num_tasks                18          
compute_ruptures_sent.gsims               3,222       
compute_ruptures_sent.monitor             24,498      
compute_ruptures_sent.sources             1,012,310   
compute_ruptures_sent.src_filter          12,780      
compute_ruptures_tot_received             80,714      
hazard.input_weight                       13,980      
hazard.n_imts                             1           
hazard.n_levels                           40          
hazard.n_realizations                     8           
hazard.n_sites                            1           
hazard.n_sources                          22          
hazard.output_weight                      320         
hostname                                  gem-tstation
require_epsilons                          False       
========================================= ============

Specific information for event based
------------------------------------
======================== =====
Total number of ruptures 13   
Total number of events   13   
Rupture multiplicity     1.000
======================== =====

Estimated data transfer for the avglosses
-----------------------------------------
1 asset(s) x 6 realization(s) x 1 loss type(s) x 1 losses x 8 bytes x 16 tasks = 768 B

Exposure model
--------------
=============== ========
#assets         1       
#taxonomies     1       
deductibile     absolute
insurance_limit absolute
=============== ========

======== ===== ====== === === ========= ==========
taxonomy mean  stddev min max num_sites num_assets
M1_2_PC  1.000 NaN    1   1   1         1         
======== ===== ====== === === ========= ==========

Slowest sources
---------------
====== ========= ============ ============ ========= ========= =========
grp_id source_id source_class num_ruptures calc_time num_sites num_split
====== ========= ============ ============ ========= ========= =========
1      10        AreaSource   4,482        0.0       1         0        
1      3         AreaSource   3,509        0.0       1         0        
3      5         AreaSource   2,349        0.0       1         0        
0      0         AreaSource   24,435       0.0       1         0        
1      5         AreaSource   2,349        0.0       1         0        
3      8         AreaSource   1,440        0.0       1         0        
1      8         AreaSource   1,440        0.0       1         0        
3      4         AreaSource   1,280        0.0       1         0        
3      10        AreaSource   4,482        0.0       1         0        
1      4         AreaSource   1,280        0.0       1         0        
2      2         AreaSource   19,923       0.0       1         0        
1      6         AreaSource   4,123        0.0       1         0        
0      1         AreaSource   4,163        0.0       1         0        
3      9         AreaSource   2,508        0.0       1         0        
1      9         AreaSource   2,508        0.0       1         0        
0      2         AreaSource   19,923       0.0       1         0        
3      3         AreaSource   3,509        0.0       1         0        
2      1         AreaSource   4,163        0.0       1         0        
1      7         AreaSource   1,690        0.0       1         0        
2      0         AreaSource   24,435       0.0       1         0        
====== ========= ============ ============ ========= ========= =========

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
AreaSource   0.0       22    
============ ========= ======

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
compute_ruptures   1.683 0.739  0.319 2.753 18       
================== ===== ====== ===== ===== =========

Slowest operations
------------------
================================ ========= ========= ======
operation                        time_sec  memory_mb counts
================================ ========= ========= ======
total compute_ruptures           30        0.695     18    
managing sources                 2.151     0.0       1     
reading composite source model   1.136     0.0       1     
saving ruptures                  0.085     0.0       18    
filtering composite source model 0.011     0.0       1     
filtering ruptures               0.004     0.0       14    
setting event years              0.004     0.0       1     
reading exposure                 0.003     0.0       1     
store source_info                0.001     0.0       1     
reading site collection          9.775E-06 0.0       1     
================================ ========= ========= ======